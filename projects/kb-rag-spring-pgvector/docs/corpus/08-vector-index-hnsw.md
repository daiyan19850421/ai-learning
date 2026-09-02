# HNSW 向量索引

HNSW（Hierarchical Navigable Small World）是 pgvector 支持的近似最近邻索引。

特点：查询快、召回高，适合在线 RAG；构建索引占用内存与 CPU。

Spring AI PgVector 配置项：`spring.ai.vectorstore.pgvector.index-type=HNSW`。

距离类型常用 `COSINE_DISTANCE`，与归一化 embedding 配合。

无索引时大规模向量表会 Seq Scan，P95 延迟随数据量线性上升。
