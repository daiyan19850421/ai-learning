# kb-rag-spring-pgvector

Week 1 目标：Spring AI + PostgreSQL/pgvector 最小 RAG，10 份固定语料可问答并带引用。

详细步骤见：[notes/learn-and-work/kb-rag-spring-pgvector/001-week1-setup.md](../../notes/learn-and-work/kb-rag-spring-pgvector/001-week1-setup.md)

## 快速启动

```powershell
# 1. 数据库
docker compose up -d

# 2. API 密钥
copy .env.example .env
# 编辑 .env 填入 SPRING_AI_OPENAI_API_KEY 等

# 3. 启动（需 JDK 21）
.\mvnw.cmd spring-boot:run

# 4. 入库 & 问答
curl -X POST http://localhost:8080/api/ingest
curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"question\":\"HikariCP 默认连接池大小是多少？\"}"
```

## 技术栈

- Java 21, Spring Boot 3.4, Spring AI 1.0
- PostgreSQL 16 + pgvector
- OpenAI 兼容 API（Chat + Embedding）

## 目录

```text
docs/corpus/     # 10 份固定语料
src/main/java/   # ingest + chat
docker-compose.yml
```
