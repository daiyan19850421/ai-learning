# PostgreSQL pgvector

pgvector 是 PostgreSQL 的向量相似度搜索扩展。

安装：`CREATE EXTENSION vector;`

常用列类型：`vector(n)`，n 为 embedding 维度。

索引类型包括 IVFFlat 和 HNSW；HNSW 查询延迟通常更低，适合在线检索。

Spring AI 可通过 `spring-ai-pgvector-store-spring-boot-starter` 自动建表并写入向量。
