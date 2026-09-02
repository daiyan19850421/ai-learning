# HikariCP 连接池

HikariCP 是 Spring Boot 2.x 起默认的 JDBC 连接池。

关键参数：

- `maximum-pool-size`：最大连接数，默认 10
- `connection-timeout`：获取连接超时（毫秒）
- `idle-timeout`：空闲连接回收时间

连接池过小会导致请求等待；过大则占用数据库 `max_connections`。

监控可关注：活跃连接数、等待线程数、连接获取耗时 P99。
