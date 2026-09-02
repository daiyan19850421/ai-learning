# 30 天周计划：PostgreSQL 深度工程（性能 + 可靠性）

## 前置与链接

- 方向与约束：[001-what_should_I_learn.md](../001-what_should_I_learn.md)
- 可行性分析：[001-can_it_works.md](./001-can_it_works.md)
- 时间预算：**每天 ≥ 4 小时**，共 30 天
- 求职头衔：**Java 后端工程师**（数据库性能 / 可靠性专项）

---

## 30 天终态产出（验收清单）

完成本计划后，你应能拿出以下可追问验证的材料：

| # | 产出 | 路径 / 形式 | 完成 |
|---|------|-------------|------|
| 1 | 慢查询案例 ×2 | `cases/01-*.md`、`cases/02-*.md` | [ ] |
| 2 | Spring Boot + PG 压测仓库 | GitHub 仓库 `pg-governance-lab`（名可自定） | [ ] |
| 3 | 故障演练 runbook ×3 | `runbook/` 目录 | [ ] |
| 4 | 5 道口述题答案 | `interview/05-oral-qa.md` | [ ] |
| 5 | 简历「数据库专项」一节 | 本地简历文件 | [ ] |
| 6 | 目标 JD 追踪表（≥20 条） | `job-tracker.md` | [ ] |

---

## 时间分配模板（每日 4h）

| 块 | 时长 | 内容 |
|----|------|------|
| A 读文档 | 45–60 min | PG 官方文档 / 博客 / 源码外阅读 |
| B 动手实验 | 90–120 min | SQL、压测、复现故障 |
| C 写笔记 / 代码 | 60–90 min | 案例文档、README、runbook |
| D 求职（第 15 天起） | 30–45 min | 筛 JD、投递、改简历 |

某天实验顺利可压缩 A、加大 B；某天写不出笔记则先完成 B 的原始输出（截图、EXPLAIN 文本），次日再写 C。

---

## Day 0：环境搭建（计划开始前或第 1 天上午）

### 软件

| 组件 | 版本建议 | 用途 |
|------|----------|------|
| PostgreSQL | 16+ | 主实验库 |
| Docker Compose | 最新稳定 | 一键起 PG + 监控（可选） |
| JDK | 17 或 21 | Spring Boot |
| IDE | 现有即可 | Java + SQL |
| psql / DBeaver | — | 执行 EXPLAIN |
| k6 或 JMeter | 二选一 | 压测（k6 脚本短、CI 友好） |

### 仓库与目录结构（建议）

在本项目或独立 GitHub 仓库中建立：

```text
pg-governance-lab/
├── docker-compose.yml          # PG 16 + pg_stat_statements
├── sql/
│   ├── schema.sql              # 业务表结构
│   ├── seed.sql                # 测试数据（≥100 万行级）
│   └── queries/                # 待优化 SQL
├── app/                        # Spring Boot 3.x
│   └── ...                     # HikariCP、MyBatis/JPA 任选
├── bench/                      # k6 或 JMeter 脚本
├── cases/                      # 慢查询案例（可同步到 notes）
├── runbook/                    # 故障演练文档
└── README.md                   # 复现步骤 + 结果摘要
```

### PostgreSQL 最小配置

`postgresql.conf` 中确保开启（Docker 可用 custom conf 挂载）：

```ini
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
log_min_duration_statement = 200   # 可选：200ms 以上记入日志
```

验证：

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT count(*) FROM pg_stat_statements;
```

### 样例业务场景（与 Java 后台履历一致）

采用 **内部后台 + 订单 / 用户 / 审计日志** 模型，便于面试讲述：

- `users`（10 万）
- `orders`（100 万）
- `order_items`（300 万）
- `audit_logs`（500 万，故意制造慢查询温床）

`seed.sql` 用 `generate_series` 批量插入即可，不要求真实业务，但**必须在 README 写明行数**。

**Day 0 完成标准**：`docker compose up` 后 PG 可连、`pg_stat_statements` 有数据、Spring Boot 能跑通一个查询接口。

---

## 第 1 周：执行计划与索引（Day 1–7）

**周目标**：会读 `EXPLAIN (ANALYZE, BUFFERS)`，会用 `pg_stat_statements` 找热点 SQL，完成 **2 篇慢查询优化案例**。

| 天 | 主题 | 任务（4h） | 当日产出 |
|----|------|------------|----------|
| **1** | EXPLAIN 基础 | 读 [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)；对 `orders` 做 3 条故意糟糕的查询（无索引、`LIKE '%xx'`、`OR` 条件）并 `EXPLAIN ANALYZE` | `cases/00-explain-cheatsheet.md`（自写速查：Seq Scan / Index Scan / Bitmap / cost / actual time） |
| **2** | B-Tree 索引 | 读索引文档 B-Tree 一节；为 Day1 的 3 条 SQL 逐一加索引，记录 **优化前后** plan 与耗时 | 案例 1 初稿：`cases/01-order-list-slow.md` |
| **3** | 复合索引与顺序 | 实验 `(status, created_at)` vs `(created_at, status)`；理解 **最左前缀** 与 **索引列顺序** | 更新案例 1：加「为何选这个顺序」一节 |
| **4** | 索引失效场景 | 对同一表验证：`函数包裹列`、`隐式类型转换`、`OR` 跨列、`NOT IN` / 低选择性列；每类 1 个例子 | `cases/02-index-pitfalls.md`（半篇） |
| **5** | pg_stat_statements | 跑一轮 k6 打接口；`SELECT query, calls, mean_exec_time, total_exec_time FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10`；选 1 条业务 SQL 深挖 | 案例 2 初稿：`cases/02-audit-log-scan.md` |
| **6** | 覆盖索引与回表 | 实验 `INCLUDE`、理解 `Index Only Scan` 条件；对比「宽索引」与「回表」代价 | 完成案例 2 |
| **7** | 周复盘 | 整理 2 篇案例为统一模板（见下）；自测 3 道口述小题 | 案例 1、2 定稿；README 增「Week1 结论」 |

### 案例文档模板（每篇必含）

```markdown
# 案例标题

## 现象
- 接口 / SQL 文本
- 业务场景（一句话）

## 数据规模
- 表名、行数、现有索引

## 优化前
- EXPLAIN (ANALYZE, BUFFERS) 全文
- 耗时（ms）、扫描行数

## 根因
- 为何慢（2–3 句，指向具体 plan 节点）

## 方案
- DDL / SQL 改写
- 取舍（写放大、维护成本）

## 优化后
- 新 EXPLAIN + 耗时对比表

## 若在生产
- 如何灰度验证、如何回滚索引
```

### 第 1 周口述自测（先写下来，第 4 周精炼）

1. `Seq Scan` 在什么情况下是合理选择？
2. 复合索引 `(a, b)` 能加速 `WHERE b = ?` 吗？
3. `EXPLAIN` 里 `cost` 和 `actual time` 哪个更该信？

---

## 第 2 周：连接池、事务、锁（Day 8–14）

**周目标**：理解 HikariCP 与 PG 连接模型；能复现 **连接池打满**、**长事务**、**死锁**；交付 **压测仓库 v1**。

| 天 | 主题 | 任务（4h） | 当日产出 |
|----|------|------------|----------|
| **8** | PG 连接模型 | 读文档 [Connections](https://www.postgresql.org/docs/current/connect-estab.html)；弄清 `max_connections`、每个连接是一个后端进程 | 笔记：`connection-model.md` |
| **9** | HikariCP | Spring Boot 显式配置 `maximum-pool-size`、`connection-timeout`、`leak-detection-threshold`；写 1 个故意不关闭连接的 bug 并用 leak 检测抓到 | `application.yml` 注释版 |
| **10** | 压测基线 v1 | k6 对「订单列表」接口：10 → 50 → 100 VU，记录 P95 延迟、错误率、PG 活跃连接数 | `bench/order-list.js` + `results/week2-baseline.md` |
| **11** | 连接池打满 | 将 `maximum-pool-size` 设为 5，并发 50；观察超时异常与 `pg_stat_activity` | runbook 草稿 1：`runbook/01-pool-exhausted.md` |
| **12** | 长事务 | 开启一个未提交事务并 `SELECT FOR UPDATE`；观察 vacuum 阻塞、`pg_stat_activity.state` | runbook 草稿 2：`runbook/02-long-transaction.md` |
| **13** | 锁与死锁 | 两会话制造死锁；读 `pg_locks`、`pg_stat_activity`；开启 `log_lock_waits` 看日志 | runbook 草稿 3：`runbook/03-deadlock.md` |
| **14** | 压测 v1 定稿 | 对比「索引优化前 / 后」+「连接池 5 vs 20」四组数据；更新 README | **压测仓库 v1** 打 tag `v0.1.0` |

### 压测 README 必写指标

| 场景 | 并发 | P50 | P95 | 错误率 | 池大小 | 备注 |
|------|------|-----|-----|--------|--------|------|
| 优化前 | 50 | | | | 20 | |
| 优化后 | 50 | | | | 20 | |
| 池耗尽 | 50 | | | | 5 | 预期超时 |

### 第 2 周口述自测

4. 应用连接池设多大？依据是什么？（公式：`connections = ((core_count * 2) + effective_spindle_count)` 仅作起点，强调以压测为准）
5. 长事务为什么会影响 autovacuum？

---

## 第 3 周：可靠性与可观测 + 开始投递（Day 15–21）

**周目标**：掌握复制 / 备份 / PITR **概念与实验**；会用基础监控视图；runbook 定稿；**压测 v2**；**开始投递**。

| 天 | 主题 | 任务（4h） | 当日产出 |
|----|------|------------|----------|
| **15** | 流复制概念 | Docker 起 1 主 1 从（或读文档 + 图示）；`pg_stat_replication` 看 lag | 笔记：`replication-notes.md` + 架构 ASCII 图 |
| **16** | 复制延迟演练 | 从库停 WAL 应用或大批量写入主库；观察 `replay_lag`；写排查步骤 | 更新 runbook：`runbook/04-replication-lag.md` |
| **17** | 备份与 PITR | `pg_basebackup` + WAL 归档概念；在实验环境做一次恢复（可简化为「逻辑备份 pg_dump 恢复」+ 口述 PITR 流程） | `runbook/05-backup-restore.md` |
| **18** | 可观测指标 | 整理必备视图：`pg_stat_activity`、`pg_stat_database`、`pg_stat_user_tables`、`pg_stat_statements`；可选：Docker 加 `postgres_exporter` + Grafana 单面板 | `observability/checklist.md` |
| **19** | 压测 v2 | 加入「混合读写」场景：70% 读列表 + 30% 写 audit；对比 Week2 纯读 | `results/week3-mixed.md`，tag `v0.2.0` |
| **20** | runbook 定稿 | 统一 5 篇 runbook 格式：现象 → 确认 → 止血 → 根因 → 预防 | `runbook/README.md` 索引页 |
| **21** | 求职启动 | 筛 JD、投 **5–10 个**（见下节）；简历加「数据库专项」草稿 | `job-tracker.md` 至少 10 条 |

### Runbook 模板

```markdown
# 故障：标题

## 典型现象
- 应用侧报错原文
- 监控 / 日志特征

## 快速确认（5 分钟内）
- SQL / 命令

## 止血
- 临时措施（杀连接、扩容池、降级）

## 根因分析
- 对应 pg_* 视图

## 预防与改进
- 配置、代码、索引、告警阈值
```

### 第 3 周起：投递规则

**主投关键词**：`Java` `PostgreSQL` `慢查询` / `性能优化` / `高级后端` `数据库`

**跳过信号**：`5年 DBA`、`7×24`、`驻场`、`内核`、`C++`、`源码`

**每周投递量**：第 3 周 5–10 个，第 4 周 10–15 个。

**简历专项一节（示例骨架）**：

```text
数据库性能与可靠性（PostgreSQL 专项）
- 基于 Spring Boot + HikariCP + PG 16 搭建可复现压测环境（百万级订单表）
- 通过 EXPLAIN (ANALYZE, BUFFERS) 与 pg_stat_statements 定位慢查询，P95 延迟下降 X%（填真实数字）
- 编写连接池耗尽、长事务、死锁等故障 runbook，并本地演练验证
- 技术栈：PostgreSQL、pg_stat_statements、HikariCP、k6、Docker
```

---

## 第 4 周：面试叙事与作品集封装（Day 22–30）

**周目标**：作品集可一键复现；5 道口述题定稿；模拟面试；简历定稿；稳定投递。

| 天 | 主题 | 任务（4h） | 当日产出 |
|----|------|------------|----------|
| **22** | README 打磨 | 仓库 README：背景、环境、复现命令、结果表、案例链接；陌生人 30 分钟能跑通 | README v1 |
| **23** | 口述题 1–2 | 撰写：`Seq Scan` 合理性、索引选择与权衡 | `interview/05-oral-qa.md` |
| **24** | 口述题 3–4 | 撰写：连接池 sizing、长事务 / vacuum | 同上 |
| **25** | 口述题 5 | 撰写：线上加索引如何控制风险（`CONCURRENTLY`、低峰、回滚） | 同上 |
| **26** | 模拟面试 1 | 自问自答 30 min：选案例 1 从现象讲到方案；录音或文字记录卡壳点 | `interview/mock-1.md` |
| **27** | 模拟面试 2 | 让同事 / AI 追问 runbook 任一篇；补盲区 | `interview/mock-2.md` |
| **28** | 简历定稿 | 专项数字核对（与压测结果一致）；Boss / 猎聘各上传一版 | 简历 PDF |
| **29** | 集中投递 | 投 10–15 个；更新 `job-tracker.md` 状态 | 累计 ≥20 条 JD |
| **30** | 总复盘 | 填「30 天复盘」；列后续 90 天可选深化（Patroni 实验、英语、平台岗） | `retrospective.md` |

### 5 道口述题（定稿题目）

| # | 题目 | 答题要点（提示，勿背稿） |
|---|------|--------------------------|
| 1 | 什么情况下 Seq Scan 比索引扫描更合适？ | 大比例行、小表、低选择性、索引维护成本；用你案例中的数字说明 |
| 2 | 如何判断该建什么索引？ | `pg_stat_statements` → EXPLAIN → 谓词与排序列 → 选择性 → 验证 plan |
| 3 | 连接池应该设多大？ | 无万能值；公式起点 + 压测；过大导致 PG 端连接过多 |
| 4 | 长事务有什么危害？ | 阻止 vacuum、膨胀、复制 lag、锁等待；结合 runbook 02 |
| 5 | 生产环境如何安全加索引？ | `CREATE INDEX CONCURRENTLY`、监控、超时、失败重试、避免事务块内普通 CREATE |

---

## 进度自检（每周日晚）

| 检查项 | 第 1 周 | 第 2 周 | 第 3 周 | 第 4 周 |
|--------|---------|---------|---------|---------|
| 案例 / 文档数 | ≥2 篇 | +3 runbook 草稿 | runbook 定稿 | README + 口述题 |
| 压测 tag | — | v0.1.0 | v0.2.0 | 最终数字进简历 |
| 投递数累计 | 0 | 0 | ≥10 | ≥20 |
| 能否 15 分钟讲清一个优化案例 | 试一次 | 熟练 | 流畅 | 面试就绪 |

**掉队补救**（时间不够时砍优先级）：

1. **保留**：2 个 EXPLAIN 案例、压测 v1、3 个核心 runbook（池耗尽、长事务、死锁）、简历专项
2. **可简化**：主从复制实操 → 只画架构图 + 口述；Grafana → 只保留 SQL 检查清单
3. **不砍**：第 3 周起的投递（没有投递就没有市场反馈）

---

## 推荐阅读（按周）

| 周 | 材料 |
|----|------|
| 1 | [PG 文档：Indexes](https://www.postgresql.org/docs/current/indexes.html)、[pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html) |
| 2 | [HikariCP README](https://github.com/brettwooldridge/HikariCP)、[PG：Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html) |
| 3 | [PG：High Availability](https://www.postgresql.org/docs/current/high-availability.html)、[Continuous Archiving](https://www.postgresql.org/docs/current/continuous-archiving.html) |
| 4 | 回顾自己的 cases / runbook；补投递公司技术博客中 PG 相关文章 |

---

## 30 天复盘模板（Day 30 填写）

```markdown
# 30 天复盘

## 数字
- 投递 / 回复 / 面试：
- 压测最优 P95 改善：___%
- 案例数 / runbook 数：

## 有效的事
-

## 无效或耗时的事
-

## 面试被问倒的题
-

## 后续 90 天（可选）
- [ ] Patroni 本地 HA 实验
- [ ] 英语：每周 2 篇 PG 文档精读
- [ ] 平台岗：学 postgres_exporter 告警规则
```

---

## 与父文档的对应关系

| 父文档概要 | 本计划落点 |
|------------|------------|
| 第 1 周 EXPLAIN + 索引 | Day 1–7 |
| 第 2 周连接池 + 锁 | Day 8–14，压测 v1 |
| 第 3 周可靠性 + 可观测 | Day 15–21，runbook + 压测 v2 + 投递 |
| 第 4 周面试与投递 | Day 22–30 |
| 5 道口述题 | Day 23–25 撰写，Day 26–27 模拟 |

---

## 下一步行动（今天）

- [ ] 完成 Day 0 环境（PG 16 + `pg_stat_statements` + Spring Boot 骨架）
- [ ] 生成 `seed.sql`（百万级 `orders`）
- [ ] 执行 Day 1：3 条故意慢查询 + EXPLAIN 速查表
