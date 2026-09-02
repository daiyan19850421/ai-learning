# Spring Boot 基础

Spring Boot 通过 `@SpringBootApplication` 启动，内嵌 Tomcat，默认端口 8080。

常用配置文件为 `application.yml` 或 `application.properties`，支持多 profile（如 `dev`、`prod`）。

依赖管理推荐使用 Maven 的 `spring-boot-starter-parent` 统一版本。

本地启动命令：`mvn spring-boot:run` 或运行主类的 `main` 方法。
