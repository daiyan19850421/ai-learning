# Week 1：环境清单与验收标准

## 链接

- 总览：[000-roadmap.md](../000-roadmap.md)
- 代码仓库目录：`../../../projects/kb-rag-spring-pgvector/`

---

## Week 1 唯一目标

**固定 10 份文档能问答，且回答带引用片段。**  
未完成此项，不算 Week 1 进度（MCP、压测、Agent 均推到 Week 2+）。

---

## 环境清单（Windows）

| 项 | 要求 | 你本机（已检测） |
|----|------|------------------|
| JDK | 17+（推荐 21） | OpenJDK 21 ✓ |
| Docker Desktop | 用于 PostgreSQL + pgvector | 需 **启动 Docker Desktop** 后再 `docker compose up` |
| Git | 版本管理 | Git 2.55 ✓ |
| Maven | 3.9+ | **未在 PATH 中** → 用项目内 `mvnw.cmd` 或 IDE 导入 |
| IDE | IntelliJ IDEA / VS Code + Java 插件 | 任选 |
| 大模型 API | 见下文「Embedding 与 Chat」 | 需自行申请 |

---

## 第一步：启动 PostgreSQL + pgvector

在项目根目录（含 `docker-compose.yml`）执行：

```powershell
cd d:\Projects\ai-learning\projects\kb-rag-spring-pgvector
docker compose up -d
docker compose ps
```

验收：

```powershell
docker exec -it kb-rag-pg psql -U rag -d rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec -it kb-rag-pg psql -U rag -d rag -c "\dx"
```

应看到 `vector` 扩展。

默认连接：

| 键 | 值 |
|----|-----|
| Host | localhost |
| Port | 5432 |
| Database | rag |
| User | rag |
| Password | rag_dev_only |

---

## 第二步：配置大模型 API

复制环境变量模板：

```powershell
copy .env.example .env
```

编辑 `.env`（**不要提交 Git**），任选一种：

### 方案 A：OpenAI 兼容 API（推荐，含 DeepSeek 等）

```env
SPRING_AI_OPENAI_API_KEY=你的密钥
SPRING_AI_OPENAI_BASE_URL=https://api.deepseek.com
SPRING_AI_OPENAI_CHAT_MODEL=deepseek-chat
SPRING_AI_OPENAI_EMBEDDING_MODEL=deepseek-embedding
```

> 模型名以服务商文档为准；embedding 维度须与 `application.yml` 中 `dimensions` 一致（默认 1536，若不符改配置）。

### 方案 B：Ollama 本地（无 API 费用）

1. 安装 [Ollama](https://ollama.com/)  
2. 执行：`ollama pull nomic-embed-text` 和 `ollama pull qwen2.5:7b`  
3. `.env` 中启用 Ollama 配置（见 `.env.example` 注释），并在 `application.yml` 切换 profile

Week 1 优先 **跑通**；模型质量次要。

---

## 第三步：编译与启动应用

**方式 A（推荐）**：IntelliJ IDEA 打开 `pom.xml` → Maven 面板 → Lifecycle → `spring-boot:run`  
（本机未检测到全局 `mvn` 命令，IDE 自带 Maven 即可。）

**方式 B**：生成并使用 Maven Wrapper（需 Docker 运行后执行一次）：

```powershell
docker run --rm -v "${PWD}:/app" -w /app maven:3.9-eclipse-temurin-21 mvn -N wrapper:wrapper
.\mvnw.cmd spring-boot:run
```

启动前将 `.env` 中的变量注入进程。PowerShell 示例：

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
  }
}
.\mvnw.cmd spring-boot:run
```

或在 IntelliJ：Run Configuration → Environment variables → 从 `.env` 粘贴。

启动成功后：

| 接口 | 方法 | 说明 |
|------|------|------|
| http://localhost:8080/actuator/health | GET | 健康检查 |
| http://localhost:8080/api/ingest | POST | 入库 `docs/corpus/` 下 Markdown |
| http://localhost:8080/api/chat | POST | 问答，见下 |

入库：

```powershell
curl -X POST http://localhost:8080/api/ingest
```

问答示例：

```powershell
curl -X POST http://localhost:8080/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"question\": \"Spring Boot 如何启用 pgvector？\"}"
```

---

## 第四步：准备固定 10 份语料

目录：`projects/kb-rag-spring-pgvector/docs/corpus/`

仓库已自带 10 个 `.md` 样例（Spring/Java 知识点）。Week 1 **不要换语料**，保证评估可复现。

文件名列表见：`docs/corpus/MANIFEST.md`

---

## 目录结构说明

```text
projects/kb-rag-spring-pgvector/
├── docker-compose.yml      # PG 16 + pgvector
├── pom.xml
├── .env.example / .env     # API 密钥（.env 不入库）
├── docs/
│   └── corpus/             # 固定 10 份语料
├── src/main/java/.../
│   ├── KbRagApplication.java
│   ├── config/VectorStoreConfig.java
│   ├── controller/RagController.java
│   └── service/
│       ├── IngestService.java    # 切分 + 写入向量库
│       └── RagService.java       # 检索 + 生成 + 引用
└── src/main/resources/
    └── application.yml
```

Week 1 只需理解：**ingest 写库、chat 读库+调模型**；其余模块 Week 2+ 再改。

---

## Week 1 每日建议（4h/天）

| 天 | 任务 | 验收 |
|----|------|------|
| D1 | Docker 起 PG；应用能启动；health 200 | pgvector 扩展存在 |
| D2 | 配通 API；跑通 ingest | 库中有 chunk 记录 |
| D3 | 跑通 chat；手动问 5 题 | 回答含 sources 字段 |
| D4 | 问满 10 语料各 1 题；记录 2 个答不好的 case | 笔记 2 条 |
| D5 | 写 README「如何启动」；Git 提交 | 他人可按 README 复现 |

---

## 常见问题

| 现象 | 处理 |
|------|------|
| `connection refused` 5432 | `docker compose up -d`；检查端口占用 |
| embedding 维度错误 | 改 `application.yml` 的 `spring.ai.vectorstore.pgvector.dimensions` |
| Maven 找不到 | 用 `mvnw.cmd` 或 IDE Maven 插件 |
| 回答无引用 | 检查 ingest 是否成功；调大 `top-k` |
| API 429 / 超时 | 换模型或加 retry；ingest 分批 |

---

## Week 1 结束检查表

- [ ] Docker PG + pgvector 正常
- [ ] ingest 成功，无异常栈
- [ ] 10 份语料各至少 1 个问题能答，且带 `sources`
- [ ] README 含启动步骤
- [ ] 2 条「答不好」的 case 已记笔记（Week 2 golden set 种子）

全部勾选 → 进入 [Week 2：评估集与调优](./002-week2-eval.md)（待写）。
