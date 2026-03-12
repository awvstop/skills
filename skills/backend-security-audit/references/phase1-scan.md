# Phase 1: SCAN — BSAF v3.6

## Shard 契约（每 Shard 开头强制输出）

```
### Shard {N} 契约
- 目标文件：[列出]
- 涉及路由：[列出]
- grep 命中数：X
- 适用 security_baseline：[列出]
- 预算：行数 Y/2000，TODO Z/30
```

## 三路径并行

| 路径 | 方向 | 做法 |
|------|------|------|
| **A** | 入口→下游 | 从 route_map 出发，沿调用链正向：路由→中间件→handler→service→DB。每层检查输入校验、权限、净化。 |
| **B** | Sink→上游 | 从 sink_hits（wrapper/grep/tool）出发反向追踪至 Source。对 Sink 函数执行 Find All References 定位调用方。调用方>20 时优先 Controller 层。**Path B 追踪到 DB write（INSERT/UPDATE/save）且 Source=🔴 时，标记 `[stored-source:pending]`；不终止追踪，Cross-Shard 阶段追踪该数据所有读取方是否到达危险 Sink。** |
| **C** | 结构/语义 | C1 认证覆盖率；C2 BOLA 三点对齐+Mass Assignment；C3 业务逻辑 checklist；C4 敏感入口 checklist（AuthN/AuthZ/Ownership/Tenant）；C5 敏感流程（checks-business）；**C6 Secret Propagation**（见下）。 |

### C6 Secret Propagation（Path C 子检查）

跟踪 🟡 来源（env/config/Vault/@Value）是否泄露到不安全上下文：

| 泄露路径 | 风险 |
|---------|------|
| secret 直接写入 API 响应体 / 序列化 Entity 含凭证字段 | 🔴 |
| logger.info/debug(secret) / catch(e) { log(e.message含凭证) } | 🟠 |
| 模板渲染 `{{config.DATABASE_URL}}` / `${env.SECRET_KEY}` | 🔴 |
| error response 含 stack trace 暴露连接串 | 🟡 |
| @Value 注入值通过 Actuator /env 暴露 | 🔴（见 frameworks-java Actuator 段） |

**操作**：grep `process\.env\|System\.getenv\|Environment\.getProperty\|@Value` → 追踪每个读取点的最终去向；到达 response/log/template → 记录 TODO（sink: data_exposure）。

**Shard 须引用 security_baseline**：结论前先对照 baseline 确认无全局覆盖。

## LSP 优先追踪

1. 变量来自 import → **Go to Definition** → 读函数体
2. 需知谁调用 → **Find All References** → 筛生产代码
3. 中间件/装饰器 → Go to Definition 确认行为
4. 以上无果 → grep 函数名
5. 仍无果 → `[trace:unresolved]` + Candidate
6. 语义概念搜索 → @Codebase → `[source:semantic-search]`

## 轻量 Taint Propagation

| 传播类型 | 规则 |
|---------|------|
| 赋值 `x = req.body` | x 继承 🔴 |
| 解构 `{id} = req.params` | id 继承 🔴 |
| 对象包装 `{id: req.params.id}` | 包装对象继承 🔴 |
| 函数返回 `q = buildQuery(req.body)` | q 标 ⚪ → 追踪 buildQuery |
| 模板字面量 `` `WHERE id=${id}` `` | 整体继承 id 信任 |
| 展开 `{...req.body}` | 目标继承 🔴 |
| 拼接 `"..." + tainted` | 整体继承 tainted 信任 |

taint_set 按整体信任级别维护，不做字段级区分。自定义函数须跳转读函数体确认。

**追踪深度上限**：单条污点链追踪 ≤ 5 层函数调用；达上限仍未到达 Sink/净化器 → 标 `[trace:depth-limit]` + Candidate。跨文件/跨模块边界计为 1 层。到达 DB driver / 框架底层 / 外部 SDK → 自动终止（视为 Sink 已到达）。

## 预算

- 已用 >80% 且 P0/P1 未完 → 对 P3+ 做快速确认再延后
- 已用 >90% → 仅 P0，余入未扫描清单
- Path C 不占行数预算，始终执行

## 噪声过滤（grep 后立即执行）

- 注释/docstring → [noise:comment]
- .d.ts/.pyi/type 声明 → [noise:typedef]
- import/require（非动态） → [noise:import]
- 同函数同 Sink 多次命中 → 合并
- 配置 schema 字段定义 → [noise:config-schema]
- ORM 安全方法（非 .raw()） → [excluded:safe-orm]
- `__tests__/` / `*.test.*` / `*.spec.*` / `*.mock.*` 测试夹具 → [noise:test-fixture]
- OpenAPI/Swagger `.yml`/`.yaml` schema 定义 → [noise:api-schema]
- protobuf/gRPC 生成文件 / `*.pb.go` / `*_pb2.py` / `*.pb.java` → [noise:generated-types]

## Shard 结束 [Reflection]（≤10 行）

Path C 覆盖 | P0/P1 未追踪数 | ⚪ unknown 列表 | 噪声率 | 预算余量 | 降级区命中
