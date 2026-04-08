# Async Surfaces — BSAF v3.6

> Queue/Webhook/Cron/DLQ/Event。自包含。

## 每个异步入口须检查

| 维度 | 要点 |
|------|------|
| **入口** | 公网可投递→🔴；内网→🟠 |
| **payload 信任** | 签名/来源校验；解析后直传 DB/HTTP → 🔴 |
| **auth context** | 任务携带 user_id/tenant_id → 执行时用该身份授权 |
| **tenant context** | 多租户下 job 带 tenant_id → consumer 按租户隔离 |
| **幂等/去重** | 重试致重复扣款/发货 → 🔴；检查 messageId/eventId/idempotency-key/dedup-key 字段是否存在且被 consumer 检查 |
| **retry** | 无上限/退避 → DoS 🟡 |
| **DLQ/replay** | 重放致重复副作用 → 🟡；需审批 |

## 检查点

1. **Webhook**：签名验证(HMAC/secret) → 未验证 🔴。重放防护(timestamp+nonce) → 无 🟡。
2. **Queue consumer**：payload 校验；禁信任 payload 内 user_id 做授权。
3. **Cron**：仅内网/受控触发；多租户带 tenant 范围。
4. **Retry/幂等**：敏感操作(支付/发货)须有幂等 key：`messageId` / `eventId` / `idempotency-key` / `x-dedup-id`；consumer 须先查去重表再执行副作用；去重 key 须有过期时间防永久占用。
5. **DLQ**：重放需审批，记审计日志。

## Source 信任

外部 MQ/公网可投递 → 🔴。内部定时/内部队列 → 🟠-low。

## Java/Spring 异步（检测到 Spring 时）

| 入口 | 检查 |
|------|------|
| **@Scheduled** | 仅内网/受控；多租户带 tenant 范围；无敏感副作用泄露 |
| **@Async** | SecurityContext 不传播 → 异步方法内无 user 上下文 🔴；需 `TaskDecorator` 传递或显式传参 |
| **Spring Cloud Stream** | binder 配置、consumer group、payload 信任同 Queue；死信/重试策略 |
| **@EventListener** | 事件来源可信；异步监听器同 @Async 上下文 |
| **Reactor/R2DBC** | 订阅链中敏感操作须在认证上下文内执行 |
| **Java 21+ Virtual Threads** | SecurityContextHolder(MODE_INHERITABLETHREADLOCAL) 在 VT 复用时跨请求泄露 → 🔴；@Async 无 ContextPropagatingTaskDecorator → 上下文丢失 🔴；自定义 ThreadLocal\<TenantId\> 跨用户泄露 🔴；MDC 错乱 🟡。须 ScopedValue 或按请求隔离；TaskDecorator 传播。详见 frameworks-java.md「Virtual Threads」。 |
| **Quartz Scheduler** | `JobDataMap` = Source（🟠-low，内部定时）；若 JobDataMap 值来自外部输入（API 触发调度）→ 🔴；JDBCJobStore 存储 job 数据的 SQL 拼接（旧版 Quartz）→ SQL 注入 🟡；`JobDetail.getJobClass()` 加载用户指定类名 → 不安全反射 🔴；Scheduler 管理端点无认证 → 🔴 |
