---
name: frontend-security-audit
description: >
  仅审计前端/浏览器端代码（CEVF v6）。Scoped to frontend only；后端请用「后端安全审计」Skill。
  **入口：用户只需说「扫描当前项目」「前端安全审计」「对当前项目执行前端安全审计」即启动全自动流程**，无需指定路径或 scope。
  Triggers: 扫描当前项目, 前端安全审计, 前端漏洞扫描, frontend security audit, XSS检查, 前端代码安全review。
  用户明确请求「后端审计」「API 审计」「服务端审计」时不适用本 Skill。
globs:
  - "src/**/*.{js,jsx,ts,tsx,vue,svelte,html,ejs,hbs,pug}"
  - "lib/**/*.{js,jsx,ts,tsx}"
  - "utils/**/*.{js,jsx,ts,tsx}"
  - "services/**/*.{js,jsx,ts,tsx}"
  - "pages/**/*.{js,jsx,ts,vue}"
  - "app/**/*.{js,jsx,ts,tsx}"
  - "components/**/*.{js,jsx,ts,tsx,vue,svelte}"
  - "*.{env,npmrc,yarnrc}"
  - "package.json"
alwaysApply: false
---

# Frontend Security Audit — CEVF v6

> **全自动**：用户只需说 **「扫描当前项目」** 或 **「前端安全审计」**，即从 Phase 0 自动执行到报告输出。

> **仅最后输出报告**：Phase 0/1/2 及 Cross-Shard 中间内容**均不向用户展示**；用户只看到最终确认报告。

> 可选参数：`fast` / `diff` / `include_fix=true` · `phase=N` / `从Shard N开始` / `暂停` / `修复V-001`

---

## CONTRACT

**范围：** 仅前端（浏览器运行、渲染层、前端构建与依赖）；后端由「后端安全审计」Skill 负责。

**角色：** 资深 Web 前端安全工程师，不修改项目代码，仅输出审计发现。Search-first · Sink-first · 热区聚焦 · 全自动续接。

**审计护栏：** 审前净化、只读约束、派生产物规则见 `references/guardrails.md`（强制加载）。本 Skill 仅允许写入 `.bsaf/cevf-todo.md`（`persist_todo=false` 关闭）。

| 参数 | 必填 | 说明 |
|------|------|------|
| repo_path | ✅ | 「当前项目」= 工作区根路径；否则为指定路径 |
| scope | ❌ | 未指定时由 Phase 0.0 自动识别前端根 |
| audit_mode | ❌ | `fast`(≤10文件/1层) · `deep`(热区聚焦/≤8层,**默认**) · `diff`(变更+deps+反向引用方) |
| scope_strategy | ❌ | `auto`(默认) · `critical_path` · `sink_density` |
| include_fix | ❌ | 附修复方案,默认false |
| output_format | ❌ | `markdown`(默认) / `json` |
| phase | ❌ | 手动指定0/1/2 |
| persist_todo | ❌ | false→关闭 TODO 落盘；默认 true |

**跳过：** dist/ build/ node_modules/ .next/ .nuxt/ .svelte-kit/ coverage/ vendor/ generated/ report/ .audit/ .bsaf/ __tests__/ __mocks__/ cypress/ e2e/ *.test.* *.spec.* *.stories.* *.min.js *.d.ts *.map `security-audit-report*.md`；单文件 >2MB 跳过。`.env.example`/`.env.sample`/`.env.template` **不跳过**。

**输出：** 唯一产出为对话中的最终报告。

**混合项目：** monorepo 等由 Phase 0.0 自动识别前端根目录，无需用户指定。

### 五条红线

1. **不臆断** — 不假设已净化；API响应≠安全；看到净化≠有效
2. **不编造** — 未读取文件不引用；路径来自实际文件树；行号不确定标「近似」
3. **不遗漏** — Sink匹配全标记；confirmed+excluded+pending=TODO总数；超限项记入「未扫描清单」
4. **不凭空定位** — 以「代码片段+组件/函数名」定位，行号辅助
5. **不补全** — 函数/API返回值须通过读取代码确认；推断标`[inferred]`且证据降E2

### Grep局限声明（计入报告）

文本grep无法捕获：动态属性拼接 · 变量别名 · 装饰器/HOC包裹 · 运行时生成Sink。报告覆盖度基于grep命中。

---

## PHASE ROUTER

```
IF recon-profile 不存在 → Phase 0
ELIF todo-list 有未扫描分片 → Phase 1
ELIF 所有分片Phase 1完成且未做cross-shard reconciliation → Cross-Shard
ELIF todo-list 有 pending 项 → Phase 2
ELSE → 已完成
```

**自驱动协议：**
1. 完成当前 Phase/Shard 后**自动进入下一步**，不输出中间产物
2. 中间结构化产物（recon-profile、todo-list、判定卡）仅内部保持
3. **仅 Phase 2 全部完成时**生成最终报告输出给用户
4. 同一 turn 可连续多步；预算不够时下一 turn 自动续接

**TODO 持久化：** Phase 1 每 Shard 完后 append 写入 `.bsaf/cevf-todo.md`；Phase 2 从该文件加载。

---

## PHASE 0: RECON（不读源码正文）

**完整决策逻辑见 `references/phase-0-recon.md`。** 骨架如下：

| 子步骤 | 动作 | 产出 |
|--------|------|------|
| 0.0 | 自动识别 frontend_root（monorepo/混合/纯前端） | `frontend_root` 写入 recon-profile |
| 0.1 | 技术栈识别（≤5文件） | stack_profile JSON |
| 0.2 | Search-first Sink 预扫（grep/rule-index.md） | sink_hits + 过滤 |
| 0.3 | 分片计划（热区聚类） | shard_plan |
| 0.4 | 自检 | recon-profile 完成 → 进入 Phase 1 |

---

## PHASE 1: SCAN（按分片，每turn单片）

### 1.0 AST-Lite Import感知
对当前分片Sink命中文件读头部import/require（≤20行/文件）→ 局部依赖子图。

### 1.1 JIT规则加载
读 `references/rule-index.md` §route-table → 按需加载对应 reference。常识 Sink（innerHTML/eval/v-html/dangerouslySetInnerHTML/document.write）内置知识。

### 1.2 Sink-first扫描
加载 `references/scan-strategy.md` → 按 Sink-first 流程执行。

### 1.3 自检 + todo-list
每 Shard 输出 todo-list（格式含 Pri/文件/Sink/Source/信任/证据/TRACE/status）。**不输出到对话**。

---

## CROSS-SHARD RECONCILIATION

所有分片 Phase 1 完成后执行：汇总 todo-list → 识别跨 Shard 数据流 → 合并依赖链 → 更新 todo-list。不输出中间内容，直接进入 Phase 2。

---

## PHASE 2: VERIFY（每批5-8个TODO）

### 2.0 加载决策树
读 `references/verify-decision-tree.md` → 判定卡格式 + 决策流程(Step 1-3) + 严重性/证据模型。

### 2.1 批次执行
按决策树逐条验证 → 内部填写判定卡 → 更新 status（confirmed/excluded/pending）。

### 2.2 F0全局自检（最终报告前）
- 全部TODO: confirmed + excluded + pending = 总数
- 所有V-### 有fingerprint
- 局限性声明已包含
- 未覆盖区域已列出

报告按 `references/rule-index.md` §report-template 输出 → **此时才向用户输出**。

---

## DIFF MODE + 执行边界

详细参数表与工作流见 **`references/execution-bounds.md`**。

核心约束：`deep` 模式每片 ≤15文件/≤2000行/≤30 TODO；追踪至确认Source或8层。预算耗尽时 P0 优先，余项记入未扫描清单。

---

## 后续指令

修复V-001 → 加载references/fix-strategies.md · V-002为误报 → 排除 · 扩展U-001 → 读取建议文件 · 继续Shard N · 导出JSON · 对比历史 · OWASP分类
