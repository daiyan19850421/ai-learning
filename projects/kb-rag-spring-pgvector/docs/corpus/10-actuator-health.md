# Actuator 健康检查

Spring Boot Actuator 提供运维端点。

启用：`spring-boot-starter-actuator`，配置 `management.endpoints.web.exposure.include=health`。

访问：`GET /actuator/health` 返回 `{"status":"UP"}` 表示应用进程正常。

注意：health UP 不代表数据库或 LLM API 可用；Week 2 可扩展 readiness 探针。

Docker 部署时 health 可用于容器重启策略。
