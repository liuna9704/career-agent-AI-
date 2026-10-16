import hashlib
import math
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()


class EmbeddingError(RuntimeError):
    pass


class EmbeddingClient:
    """OpenAI-compatible embedding client with deterministic local fallback."""

    def __init__(self) -> None:
        self.api_key = os.getenv("EMBEDDING_API_KEY", "").strip()
        self.base_url = os.getenv("EMBEDDING_BASE_URL", os.getenv("LLM_BASE_URL", "")).strip().rstrip("/")
        self.model = os.getenv("EMBEDDING_MODEL", "").strip()
        self.timeout = float(os.getenv("EMBEDDING_TIMEOUT", "60"))
        self.fallback_enabled = os.getenv("EMBEDDING_MOCK_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}
        self.local_dimension = int(os.getenv("EMBEDDING_FALLBACK_DIMENSION", "384"))

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    @property
    def mode(self) -> str:
        return self.model if self.configured else "local-hash-v1"

    async def embed(self, text: str) -> list[float]:
        if self.configured:
            try:
                endpoint = self.base_url
                if not endpoint.endswith("/embeddings"):
                    endpoint = f"{endpoint}/embeddings"
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json={"model": self.model, "input": text},
                    )
                    response.raise_for_status()
                    return [float(value) for value in response.json()["data"][0]["embedding"]]
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                raise EmbeddingError("Embedding服务调用失败，请检查配置或稍后重试") from exc
        if not self.fallback_enabled:
            raise EmbeddingError("Embedding尚未配置，且本地降级已关闭")
        return self._local_hash_embedding(text)

    def _local_hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.local_dimension
        lowered = text.lower()
        latin_tokens = re.findall(r"[a-z0-9+#.]{2,}", lowered)
        chinese = "".join(re.findall(r"[\u4e00-\u9fff]", lowered))
        tokens = latin_tokens + [chinese[index : index + 2] for index in range(max(0, len(chinese) - 1))]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.local_dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


embedding_client = EmbeddingClient()
