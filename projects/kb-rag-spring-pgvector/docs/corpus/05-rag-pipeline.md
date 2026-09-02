# RAG 流水线

RAG（Retrieval-Augmented Generation）分三阶段：

1. **Ingest**：文档切分 → embedding → 写入向量库
2. **Retrieve**：用户问题 embedding → 相似度检索 top-k
3. **Generate**：将检索片段作为上下文，调用 LLM 生成答案

质量受 chunk 大小、overlap、embedding 模型、top-k 影响。

生产环境需增加：引用溯源、拒答策略、评估集回归。
