# Spring AI 概览

Spring AI 提供与 Spring 生态一致的 AI 抽象：

- `ChatModel` / `ChatClient`：对话生成
- `EmbeddingModel`：文本向量化
- `VectorStore`：向量存储（含 PgVector、Milvus 等）
- `DocumentReader`：读取 PDF、Markdown 等

Advisor 机制可在调用链插入 RAG（如 `QuestionAnswerAdvisor`）。

配置 OpenAI 兼容 API 时使用 `spring.ai.openai.api-key` 与 `base-url`。
