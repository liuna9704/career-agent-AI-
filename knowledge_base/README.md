# 岗位知识库

`source_documents/` 保存岗位能力原始文档，`vector_store/` 保存FAISS索引和片段元数据。

当前支持：AI算法工程师、Java开发工程师、产品经理。

重建索引：

```powershell
cd backend
.venv\Scripts\python.exe scripts\build_knowledge_base.py
```

配置Embedding API后会使用真实向量模型；未配置时使用确定性的本地Hash Embedding，确保Demo可离线运行。
