# Phase 2: VERIFY — BSAF v3.6

> 每条 TODO 须输出判定卡后更新 status。

## Step 0 — 快速排除

| 条件 | 标记 |
|------|------|
| 函数 Find References=0（非导出） | [excluded:dead-code] |
| 仅测试文件调用 | [excluded:test-only] |
| 全局防护已确认 + 未豁免 | [excluded:global-middleware] |
| ORM 安全方法 + 未用 .raw() | [excluded:safe-orm] |

## Step 1 — Source 追踪 + 信任

按 core.md Source 信任模型。🟢 → 排除。⚪ → 继续追踪。含 [inferred] → Confidence ≤ Likely。

## Step 2 — 防护匹配

按 core.md 净化器速查。防护设计用途 ≠ Sink 上下文 → 不匹配。

**常见错配（直接确认漏洞）**：addslashes 当 SQL 防护 | parseInt 仅 | path.join 无 resolve | endsWith('.jpg') | JSON.stringify 当参数化 | isURL 当 SSRF（无 IP 校验时）| Math.random 当 crypto | === 当 timing(secret) | 仅 depthLimit 当 graphql 完整防护 | Object.freeze 浅层当 prototype 完整防护。

## Step 3 — 防护质量（五项全过才排除）

手段可靠 | 配置正确 | 位置正确 | 路径全覆盖 | 未被覆写

## Finder / Disprover（🔴 🟠 必须）

**Finder**：发现候选，走正向/反向链，给出初判。  
**Disprover**：对高危候选走反证 checklist，逐项回答写入 counter_evidence：

- □ 全局中间件是否覆盖此路由？
- □ ORM/DB 层是否有 RLS/policy？
- □ 是否有其他 service 层防护？
- □ 该代码路径生产可达？
- □ 输入是否经过未发现的净化？（读 ±50 行）

全部通过无反证 → Confirmed。任一反证成立 → 降级 Likely/Candidate。

## 高危独立视窗确认（3 类）

对以下高危候选做独立二次确认（不引用 Phase 1 记忆）：
1. auth_missing（仅写操作 POST/PUT/DELETE/PATCH）
2. SSRF（Score≥8）
3. Prompt Injection → Tool exec

两次判定一致 → Confirmed；不一致 → 取较低 Confidence。

## E3 快速升级

P0/P1 Sink 若在可读文件：同函数 ≤30 行追踪→升级；无法确认→Candidate。

## BOLA 三点对齐

| ① 路由参数 | ② 查询条件 | ③ 所有权绑定 |
|------------|------------|-------------|
| 含资源 ID | DB 用该 ID | 条件含 req.user.id |

①②③ 满足 → 安全。①② 无 ③ → BOLA（🟡读/🔴写删）。  
ID 自增整数+缺绑定 → 🔴。UUID+缺绑定 → 🟠。  
用户 ID 从 req.body 取 → 🔴。多租户须叠加 tenant_binding。

## 判定卡格式

```
TODO#: S1-003
Sink: db.query(${id}) | Source: req.params.id(🔴)
防护: 无参数化 | 匹配: ❌
counter_evidence: 无全局ORM保护, 无RLS, 路由无@Public
判定: 🔴 Confirmed | Path: B
fingerprint: src/api/user.js:getUser::db.query::sql-injection::req-params
```

## Side-Effect Sink 检查（二阶漏洞支撑）

Phase1 中标记了 `[stored-source:pending]` 的 TODO → Phase2 须执行：

1. 定位将用户输入写入存储的代码：`db.save(userInput)` / `cache.set(key, userInput)` / `queue.publish(userInput)`
2. 搜索该数据的所有**读取方**（Find All References on key/table/topic）
3. 检查读取方是否将数据传入危险 Sink（SQL/command/template/exec）
4. 若读取方在不同 Shard → 标记 `[cross-shard:second-order]`，Cross-Shard 阶段合并

| 存储类型 | 读取 Sink 优先检查 |
|---------|-----------------|
| DB 用户字段（username/email/description） | 管理后台查询拼接、报告生成、邮件模板 |
| Cache value（用户可控） | 后台 job 取出用于命令/SQL |
| Queue message | Consumer handler 内危险操作 |
| File（用户上传名） | 后台命令执行、定时任务处理 |

## 降级扫描发现

来自 migrations/seeds/templates/.env.*/__tests__ → Confidence 上限 Likely。
