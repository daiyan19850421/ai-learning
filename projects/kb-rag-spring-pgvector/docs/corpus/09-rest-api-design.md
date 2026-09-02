# REST API 设计要点

本项目 Week 1 暴露两个接口：

- `POST /api/ingest`：触发语料入库
- `POST /api/chat`：JSON body `{"question":"..."}` 返回答案与 sources

响应应包含引用来源（文件名 +  excerpt）以便审计。

错误使用标准 HTTP 状态码；4xx 客户端错误，5xx 服务端错误。

生产环境需加：鉴权、限流、请求 ID 日志。
