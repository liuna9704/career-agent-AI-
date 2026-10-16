import asyncio
import hashlib
import json
import logging
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

import faiss
import numpy as np

from app.core.embedding import EmbeddingClient, embedding_client

logger = logging.getLogger(__name__)

JOB_CATALOG = {
    "ai_engineer": {"name": "AI算法工程师", "description": "算法建模、实验评估与模型工程落地"},
    "java_engineer": {"name": "Java开发工程师", "description": "服务端开发、数据存储与分布式工程实践"},
    "product_manager": {"name": "产品经理", "description": "用户洞察、产品设计与跨团队交付"},
}


@dataclass
class KnowledgeDocument:
    job_key: str
    job: str
    source: str
    content: str


@dataclass
class KnowledgeChunk:
    job_key: str
    job: str
    ability: str
    source: str
    content: str


class RAGService:
    def __init__(self, client: EmbeddingClient | None = None) -> None:
        self.client = client or embedding_client
        self.project_root = Path(__file__).resolve().parents[3]
        self.source_dir = self.project_root / "knowledge_base" / "source_documents"
        self.store_dir = self._resolve_store_dir(self.project_root / "knowledge_base" / "vector_store")
        self.index_path = self.store_dir / "competencies.faiss"
        self.metadata_path = self.store_dir / "metadata.json"
        self._index = None
        self._chunks: list[KnowledgeChunk] = []
        self._lock = asyncio.Lock()

    @staticmethod
    def _is_ascii(path: Path) -> bool:
        try:
            str(path).encode("ascii")
            return True
        except UnicodeEncodeError:
            return False

    @classmethod
    def _resolve_store_dir(cls, default_dir: Path) -> Path:
        """返回可安全读写的向量库目录。

        faiss-cpu 在 Windows 上使用窄字符文件 API，索引路径一旦包含中文等
        非 ASCII 字符，read_index/write_index 都会失败（报错为误导性的
        "No such file or directory"）。因此项目路径非 ASCII 时，把索引落到
        系统临时目录；也可以用 VECTOR_STORE_DIR 显式指定。
        """
        override = os.getenv("VECTOR_STORE_DIR", "").strip()
        if override:
            return Path(override).expanduser()
        if cls._is_ascii(default_dir):
            return default_dir
        fallback = Path(tempfile.gettempdir()) / "career_agent_vector_store"
        logger.warning(
            "项目路径包含非 ASCII 字符，faiss 无法读写该路径下的索引，"
            "向量库目录改用：%s（可用 VECTOR_STORE_DIR 覆盖）",
            fallback,
        )
        return fallback

    def load_documents(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        for job_key, job_info in JOB_CATALOG.items():
            folder = self.source_dir / job_key
            for path in sorted(folder.glob("*.md")):
                documents.append(KnowledgeDocument(job_key, job_info["name"], str(path.relative_to(self.project_root)), path.read_text(encoding="utf-8")))
        return documents

    def split_documents(self, documents: list[KnowledgeDocument]) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        pattern = re.compile(r"^## (?:能力维度：)?(.+?)\s*$", re.MULTILINE)
        for document in documents:
            matches = list(pattern.finditer(document.content))
            for index, match in enumerate(matches):
                start = match.end()
                end = matches[index + 1].start() if index + 1 < len(matches) else len(document.content)
                ability = match.group(1).strip()
                content = document.content[start:end].strip()
                if content:
                    chunks.append(KnowledgeChunk(document.job_key, document.job, ability, document.source, f"岗位：{document.job}\n能力维度：{ability}\n{content}"))
        return chunks

    async def embed_documents(self, chunks: list[KnowledgeChunk]) -> np.ndarray:
        vectors = [await self.client.embed(chunk.content) for chunk in chunks]
        matrix = np.asarray(vectors, dtype="float32")
        faiss.normalize_L2(matrix)
        return matrix

    async def build_vector_store(self, force: bool = False) -> dict[str, int | str]:
        async with self._lock:
            if not force and self._load_store_if_compatible():
                return {"documents": len(self._chunks), "dimension": self._index.d, "mode": self.client.mode}
            documents = self.load_documents()
            chunks = self.split_documents(documents)
            if not chunks:
                raise RuntimeError("岗位知识文档为空")
            matrix = await self.embed_documents(chunks)
            index = faiss.IndexFlatIP(matrix.shape[1])
            index.add(matrix)
            self.store_dir.mkdir(parents=True, exist_ok=True)
            faiss.write_index(index, str(self.index_path))
            self.metadata_path.write_text(json.dumps({"mode": self.client.mode, "source_fingerprint": self._source_fingerprint(), "chunks": [asdict(chunk) for chunk in chunks]}, ensure_ascii=False, indent=2), encoding="utf-8")
            self._index, self._chunks = index, chunks
            return {"documents": len(chunks), "dimension": matrix.shape[1], "mode": self.client.mode}

    def _load_store_if_compatible(self) -> bool:
        if not self.index_path.exists() or not self.metadata_path.exists():
            return False
        try:
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.warning("向量库元数据不可读，将重建索引", exc_info=True)
            return False
        if metadata.get("mode") != self.client.mode or metadata.get("source_fingerprint") != self._source_fingerprint():
            return False
        try:
            self._index = faiss.read_index(str(self.index_path))
        except Exception:
            # 索引损坏、被截断，或路径无法被 faiss 打开 → 回退到重建，而不是让接口 500
            logger.warning("FAISS 索引读取失败，将重建向量库", exc_info=True)
            return False
        self._chunks = [KnowledgeChunk(**item) for item in metadata["chunks"]]
        return True

    def _source_fingerprint(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(self.source_dir.glob("**/*.md")):
            digest.update(str(path.relative_to(self.source_dir)).encode("utf-8"))
            digest.update(path.read_bytes())
        return digest.hexdigest()

    async def search(self, job: str, query: str, top_k: int = 3) -> list[dict]:
        job_key = self.resolve_job_key(job)
        try:
            if self._index is None or not self._chunks:
                await self.build_vector_store()
            vector = np.asarray([await self.client.embed(query)], dtype="float32")
            faiss.normalize_L2(vector)
            scores, indexes = self._index.search(vector, len(self._chunks))
        except Exception:
            # 向量检索属于增强能力，失败时降级为空结果，保证接口可用
            logger.warning("岗位知识检索失败，本次返回空结果", exc_info=True)
            return []
        results = []
        for score, index in zip(scores[0], indexes[0]):
            if index < 0:
                continue
            chunk = self._chunks[index]
            if chunk.job_key != job_key:
                continue
            results.append({**asdict(chunk), "score": round(float(score), 4)})
            if len(results) >= top_k:
                break
        return results

    def get_competencies(self, job: str) -> dict:
        job_key = self.resolve_job_key(job)
        chunks = self.split_documents(self.load_documents())
        selected = [chunk for chunk in chunks if chunk.job_key == job_key and chunk.ability != "岗位介绍" and chunk.source.endswith("competency.md")]
        return {"job": JOB_CATALOG[job_key]["name"], "competencies": [{"name": chunk.ability, "summary": chunk.content.splitlines()[2] if len(chunk.content.splitlines()) > 2 else chunk.content} for chunk in selected], "ready": bool(selected)}

    def get_competency_model(self, job: str) -> dict:
        job_key = self.resolve_job_key(job)
        path = self.source_dir / job_key / "competency_model.md"
        if not path.exists():
            return {"job": JOB_CATALOG[job_key]["name"], "competencies": []}
        content = path.read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## 能力维度：(.+?)\s*$", content, re.MULTILINE))
        competencies = []
        for index, heading in enumerate(headings):
            block = content[heading.end() : headings[index + 1].start() if index + 1 < len(headings) else len(content)]
            fields: dict[str, str] = {}
            for key in ("能力描述", "评价指标", "面试验证问题", "评分标准"):
                match = re.search(rf"^- {key}：(.+)$", block, re.MULTILINE)
                fields[key] = match.group(1).strip() if match else ""
            split_items = lambda value: [item.strip() for item in re.split(r"[；;]", value) if item.strip()]
            competencies.append({
                "name": heading.group(1).strip(), "description": fields["能力描述"],
                "indicators": split_items(fields["评价指标"]),
                "interview_points": split_items(fields["面试验证问题"]),
                "score_rule": fields["评分标准"],
            })
        return {"job": JOB_CATALOG[job_key]["name"], "competencies": competencies}

    @staticmethod
    def resolve_job_key(job: str) -> str:
        if job in JOB_CATALOG:
            return job
        for key, value in JOB_CATALOG.items():
            if value["name"] == job:
                return key
        raise KeyError(job)


rag_service = RAGService()
