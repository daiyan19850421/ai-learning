# EXPLAIN ANALYZE

`EXPLAIN ANALYZE` 执行 SQL 并输出实际运行计划与耗时。

示例：`EXPLAIN (ANALYZE, BUFFERS) SELECT ...`

关注节点类型：Seq Scan、Index Scan、Bitmap Index Scan。

`actual time` 第一列是 startup，第二列是 total；`rows` 对比 `rows=估计` 可发现统计信息过期。

优化慢查询顺序：确认谓词有索引 → 避免函数包裹列 → 检查连接顺序与 Nested Loop 成本。
