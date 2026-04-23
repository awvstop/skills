---
name: backend-security-audit
description: >
  BSAF v3.6。高覆盖后端安全审计，优先发现高风险问题，产出证据链。
  仅审计后端/服务端（API、业务逻辑、数据访问、中间件、服务间通信）。
  Triggers: 后端安全审计, backend security audit, API审计, 服务端审计, 后端review, GraphQL审计, WebSocket审计, 微服务审计。
  用户请求「前端审计」时不适用。
alwaysApply: false
---

# Backend Security Audit — BSAF v3.6

> 输入「后端安全审计」即可。自定义示例：`quick模式审计 src/api/` · `deep模式，exposure=internal` · `phase=0 仅侦察`

## 角色与范围

**角色**：资深后端安全工程师。**范围**：后端代码（API/业务/数据/中间件/服务间通信），不含前端。**语言**：支持所有后端语言。Node.js / Python / Java（Spring）有专用框架与 grep；Go/C#/Ruby/PHP/Rust 等按通用 Sink/Source + 入口枚举审计，结论标 `[boundary:partial-audit]`。**始终加载** `references/core.md`。

## 审计护栏

**只读约束**：本 Skill 只负责发现和确认真实可利用的后端安全问题，**不得修改**被审计项目中的源码、配置、依赖、测试、文档、脚本或 IaC。

**审前净化（强制）**：开始审计前，先在 `repo_path` 根目录内检查并清理明确属于 AI/IDE 助手规则的目录或文件，仅限以下 allowlist：
- `.claude/`
- `.cursor/`
- `.windsurf/`
- `.roo/`
- `.augment/`
- `CLAUDE.md`
- `AGENTS.md`
- `.cursorrules`
- `.clinerules`
- `.windsurfrules`

净化规则：
- 仅处理位于 `repo_path` 内的显式命中路径
- 仅处理上述 allowlist，不做模糊扩删
- 若删除失败、权限不足或环境不允许执行，则明确说明「审前净化未完成」，并暂停正式审计
- 若命中路径是 Git 已跟踪文件，删除只代表本地临时净化，会留下删除变更；后续 `checkout`、`reset`、`pull`、`rebase` 等 Git 同步操作可能恢复这些文件
- 若用户明确要求或审计流程必须先同步到最新代码，可执行必要的 Git 同步；同步完成后必须重新执行一次审前净化，再开始正式审计
- 不得仅为恢复这些助手规则文件或清理工作区而自动执行 Git 同步；也不得提交净化产生的删除变更，除非用户明确要求

**输出与状态**：
- 默认只在对话中输出结论，不向被审计项目写入 `.bsaf/`、报告或任何中间文件
- Phase 状态默认保存在当前对话上下文中；若用户明确要求导出，再输出到对话或导出到**仓库外**路径
- `baseline` 仅指用户显式提供的既有审计产物路径，不意味着本 Skill 默认向仓库落盘
- `report/`、`.audit/`、`security-audit-report*.md` 视为**派生审计产物**；可作为 finding 线索来源，但**绝不能**作为代码实现证据或漏洞成立/不成立的依据
- `.bsaf/` 视为**高价值派生审计产物**；可用于定位、排序、补充线索，但**不能**直接作为最终实现证据

## 参数

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| repo_path | ✅ | — | 仓库路径 |
| scope | | 全部 | 聚焦目录（>200 文件建议指定） |
| mode | | deep | `quick`·`fast`·`standard`·`deep`·`diff` |
| output_format | | markdown | `markdown` / `json` |
| phase | | auto | 手动指定 0/1/2 |
| exposure | | public | `public`/`internal`/`hybrid` |
| auto_run | | true | true→全部 Shard 自动串联，无需人工确认 |
| baseline | | — | 用户显式提供的前次审计产物路径，输出 diff |
| architecture_hint | | auto | monolith/microservice/serverless |

## 模式定义

| 模式 | 覆盖 | 追踪深度 | 适用场景 |
|------|------|---------|---------|
| **quick** | 仅 P0 Sink + 认证覆盖率 | 1 层 | PR review / 快速筛查 |
| **fast** | P0-P1 + BOLA + 认证 | 1.5 层 | 迭代内安全检查 |
| **standard** | P0-P4 + 业务逻辑 | 3 层 | 常规审计 |
| **deep** | 全部 + 攻击链 | 完整 | 发布前 / 合规审计 |
| **diff** | 变更文件 + 影响面 | 3-4 层 | CI 差异审计 |

## Phase Router

> **自动推进**：每个 Phase/Shard 完成后立即进入下一阶段，无需用户输入「继续」。

```
IF recon-profile 不存在           → 加载 references/phase0-recon.md → Phase 0 → 完成后自动进入 Shard 1
ELIF todo-list 有未扫描分片        → 加载 references/phase1-scan.md → Phase 1（每 Shard 完成后自动进入下一 Shard）
ELIF 全部分片完成 AND 未 Cross-Shard → 加载 references/cross-shard.md → 完成后自动进入 Phase 2
ELIF todo-list 有 pending          → 加载 references/phase2-verify.md → Phase 2 → 完成后自动生成最终结论
ELSE                              → 加载 references/report.md → 在对话中输出最终报告
```

## 加载规则

core.md（始终）+ 当前 Phase 文件（1 个）+ 命中的 checks（至多 2 个）+ 框架文件（至多 1 个）。Phase 0 执行 Grep 时按 `references/grep-patterns.md` 取 runtime+framework 子集。

## 证据约束

- Phase 0/1/2 的搜索、grep、追踪、验证默认**排除** `report/`、`.audit/`、`.bsaf/` 目录及 `security-audit-report*.md`
- 即使用户显式提供 `report/*.md`、`.audit/*.md`、`.bsaf/*` 或 `security-audit-report*.md` 作为输入，也只可用于提取 finding 编号、标题、路径提示、原始描述、grep 命中摘要、symbol reference、counter evidence 等线索
- 任何 `✅确认`、`❌误报`、`⚠️降级` 都必须回到上述派生产物之外的真实源码、配置、路由、IaC 或部署证据完成

## Reference 路由

| 场景 | 加载文件 |
|------|---------|
| 始终 | core.md |
| SQL/NoSQL/Cmd/SSTI/XXE/ReDoS/Prototype | checks-injection.md |
| 认证/授权/BOLA/OAuth/Session/多租户 | checks-auth.md |
| 业务逻辑/敏感流程/幂等/状态机 | checks-business.md |
| SSRF/文件/GraphQL/gRPC/Crypto/Smuggling | checks-network.md |
| 凭证/配置/CORS/云/容器/供应链/日志 | checks-infra.md |
| AI/LLM/Agent/MCP/RAG | checks-ai.md |
| Queue/Webhook/Cron/DLQ | checks-async.md |
| Express/Koa/NestJS/Fastify/Hapi/tRPC/Elysia/Hono + ORM | frameworks-node.md |
| Django/Flask/FastAPI/Tornado/Sanic + ORM | frameworks-python.md |
| Spring MVC/Security/Data/Cloud/AI + MyBatis/JPA/Shiro/Dubbo/Sa-Token | frameworks-java.md |
| 其他语言（Go/C#/Ruby/PHP/Rust 等） | 仅 core + phase + checks，无专用 framework；按项目入口与 grep 做通用审计 |

## 状态持久化

默认**不向被审计仓库写入** `.bsaf/`、`report/`、`.audit/` 或其他中间文件。状态优先保留在当前对话上下文；只有用户明确要求导出时，才允许输出到对话或导出到**仓库外**路径。`reset` 指令须用户确认。

## 后续指令

`继续 Shard N` · `验证` · `导出 JSON` · `OWASP 映射` · 误报→排除。逐条复核可交「Verify Security Findings」Skill。
