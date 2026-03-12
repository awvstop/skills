---
name: Frontend Security Audit (CEVF v6)
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

> **全自动**：用户只需说 **「扫描当前项目」** 或 **「前端安全审计」**，即从 Phase 0 自动执行到报告输出；repo_path、前端根目录、分片、Phase 续接均自动处理，无需中途输入。

> **仅最后输出报告**：Phase 0/1/2 及 Cross-Shard 的 recon、todo-list、判定卡等**中间内容均不向用户展示**；用户只会看到一份最终确认报告（security-audit-report-YYYYMMDD.md 或对话中的报告全文）。

> **仅前端**：仅当审计对象为前端仓库或用户要求「前端安全审计」时执行；若用户要求「后端/API/服务端审计」则不应使用本 Skill。

> 可选参数：`fast` / `diff` / `include_fix=true` · `phase=N` / `从Shard N开始` / `暂停` / `修复V-001`

---

## CONTRACT

**范围：** 本 Skill 仅负责**前端**（浏览器运行、渲染层、前端构建与依赖）；不含后端 API、服务端业务逻辑、数据库与基础设施。后端代码审计由独立「后端安全审计」Skill 负责，不在此执行范围内。若用户请求「后端审计」或「全栈审计」，仅执行前端部分并在报告/结论中提示对后端使用对应 Skill。

**角色：** 资深 Web 前端安全工程师。Search-first · Sink-first · 热区聚焦 · 全自动 Phase 续接。

| 参数 | 必填 | 说明 |
|------|------|------|
| repo_path | ✅ | **用户说「当前项目」「本项目」「扫描当前项目」时 = 当前工作区根路径（Cursor 打开的项目根）**，无需用户提供路径；否则为指定路径 |
| scope | ❌ | 可选；未指定时由 Phase 0.0 自动识别前端根（混合项目亦自动检测） |
| audit_mode | ❌ | `fast`(≤10文件/1层) · `deep`(热区聚焦/≤8层,**默认**) · `diff`(变更+deps+反向引用方) |
| scope_strategy | ❌ | `auto`(默认,自动分片) · `critical_path`(路由→页面→数据获取) · `sink_density`(Top-N) |
| include_fix | ❌ | 附修复方案,默认false |
| output_format | ❌ | `markdown`(默认) / `json` |
| phase | ❌ | 手动指定0/1/2 |
| context | ❌ | 补充上下文 |

**跳过：** dist/ build/ node_modules/ .next/ .nuxt/ .svelte-kit/ coverage/ vendor/ generated/ __tests__/ __mocks__/ cypress/ e2e/ *.test.* *.spec.* *.stories.* *.min.js *.d.ts *.map .env.example .env.sample .env.template；单文件 >2MB 跳过。

**输出：** 唯一正式产出为 **frontend_root 下**的 `security-audit-report-YYYYMMDD.md`（即当前项目前端根目录）；无漏洞时输出结论并含局限性声明。若文件写入不可用则报告输出到对话。

**对用户的输出约定（必须遵守）：**
- **整个审计流程中，仅在全部 Phase 完成后向用户输出一份最终报告**（即上述 security-audit-report 文件内容或文件路径）。
- **中间阶段不向用户输出任何内容**：recon-profile、分片计划、todo-list、判定卡、Phase 完成提示、Shard 进度等**均不输出到对话**，仅写入工作文件或内部保持；用户可见的只有最后的确认报告。

**混合项目：** 若仓库同时含前端与后端（如 monorepo 含 `apps/web` + `apps/api`，或根目录同时有 `src/` 与 `server/`），**由 Phase 0.0 自动识别前端根目录**，无需用户指定；后续技术栈识别、grep、分片与扫描均限定在该目录下。

### 五条红线

1. **不臆断** — 不假设已净化；API响应≠安全；看到净化≠有效；`as any`≠安全
2. **不编造** — 未读取文件不引用；路径来自实际文件树；行号不确定标「近似」；禁止编造不存在的函数/变量/grep输出
3. **不遗漏** — Sink匹配全标记；confirmed+excluded+pending=TODO总数；超限项记入「未扫描清单」禁止静默丢弃
4. **不凭空定位** — 以「代码片段+组件/函数名」定位，行号辅助
5. **不补全** — 函数/API返回值须通过读取代码确认；推断标`[inferred]`且证据降E2；未完成链路禁止推断补全

### Grep局限声明（计入报告）

文本grep无法捕获：动态属性拼接(`elem['inner'+'HTML']`) · 变量别名(`const render = el.innerHTML`) · 装饰器/HOC包裹 · 运行时生成的Sink。报告覆盖度基于grep命中，实际Sink可能更多。

---

## PHASE ROUTER

```
IF recon-profile 不存在 → Phase 0
ELIF todo-list 有未扫描分片 → Phase 1
ELIF 所有分片Phase 1完成且未做cross-shard reconciliation → Cross-Shard
ELIF todo-list 有 pending 项 → Phase 2
ELSE → 已完成；可接受后续指令（如 修复V-001、导出JSON、对比历史）
```

手动覆盖（可选）：`phase=N` / `从Shard N开始` / `暂停` / `修复V-001`

**状态持久化（中间不输出到对话）：**
```
中间产物（recon-profile、todo-list、判定结果等）不输出到对话，仅：
IF 文件写入工具可用 → 写入 frontend_root 下工作目录（如 .audit/recon-profile.md、.audit/todo-list.md）或约定路径，后续从文件读取
ELSE → 在内部/上下文中保持，不向用户展示；最终仅输出报告时再汇总
```
用户在整个流程中只会在最后看到一份报告。

**自驱动协议（自动续接 + 仅最后输出报告）：**
1. 完成当前 Phase/Shard 后**自动进入下一 Phase 或下一 Shard**，**不向用户输出**任何中间产物或进度提示。
2. 中间阶段的结构化产物（recon-profile、todo-list、判定卡）**仅写入工作文件或内部保持**，不在对话中展示；同一回复内或下一轮直接执行 Phase Router 决定的下一步，直至全部 Phase 完成。
3. **仅当 Phase 2 全部验证完成时**，生成最终报告并**作为唯一内容输出给用户**（写入 frontend_root 下 security-audit-report-YYYYMMDD.md；若文件不可用则完整报告输出到对话）。
4. **仅以下情况向用户输出非报告内容**：跨分片对账时无法从工作文件或上下文汇总 todo-list（且无文件写入）时，可简短提示用户「审计进行中，请稍候」或静默继续；用户主动说「暂停」「先到这里」时回复确认。
5. 同一 turn 内可连续执行多步，以上下文与预算为限；单 turn 内若已用预算较多，可本 turn 收尾并下一 turn 自动从下一 Shard/Phase 继续（仍不输出中间内容）。

---

## PHASE 0: RECON（不读源码正文）

### 0.0 识别前端根目录（自动检测，无需用户指定）

**目的：** 确定本审计的根路径 `frontend_root`，后续 0.1～0.4 及 Phase 1/2 的读取与 grep 均限定在此目录下，避免扫到后端代码。**若用户说「当前项目」「扫描当前项目」等未提供路径，repo_path = 当前工作区根路径（Cursor 打开的项目根）。** 前端根目录全程自动推断，不要求用户指定 scope。

**流程：**
```
若用户未提供 repo_path（如只说「扫描当前项目」「前端安全审计」）→ repo_path = 当前工作区根路径。以下均在 repo_path 下进行。

IF 用户已指定 scope（如 "apps/web"、"frontend"、"src"）→ frontend_root = scope，校验该路径下存在前端特征（package.json 含前端框架 / 有 components 或 pages 等）后沿用
ELIF 检测为 monorepo（根 package.json 含 workspaces）：
  → 列出各 workspace 路径，对每个读其 package.json（计入 5 文件限制）
  → 识别前端包：dependencies/devDependencies 含 react/vue/next/nuxt/svelte/angular 等，或 name 含 web/frontend/app/client
  → 若仅 1 个前端包 → frontend_root = 该包路径
  → 若多个前端包 → 按优先级自动取 1 个：name 或路径含 "web" > "app" > "frontend" > "client" > workspaces 数组顺序第一个；在 recon-profile 中注明「已自动选择 frontend_root=<path>，共 N 个前端包」
  → 若无明显前端包 → frontend_root = 仓库根，注明「未识别到独立前端包，以仓库根为 frontend_root」
ELIF 根目录存在典型前端+后端并列（读目录列表判断）：
  → 若存在 src/ 且（存在 server/ 或 api/ 或 backend/）→ frontend_root = "src"（常见前端在 src）
  → 否则若存在 app/ 且存在 api/ → frontend_root = "app"
  → 否则若存在 client/ → frontend_root = "client"
  → 否则若存在 frontend/ → frontend_root = "frontend"
  → 否则 → frontend_root = 仓库根，注明「未区分前后端，以仓库根为 frontend_root」
ELSE → frontend_root = 仓库根（视为纯前端或前端为主）
```

**输出到 recon-profile：** `frontend_root: "<path>"`；若由 Agent 推断则标注 `frontend_root_inferred: true`。无需等待用户确认，直接进入 0.1。

### 0.1 技术栈识别（限读≤5文件，均在 frontend_root 下）

读取 **frontend_root** 下的 package.json + 入口文件 + tsconfig/vite/webpack 配置：

```json
{
  "framework": "react|vue|angular|svelte|jquery|lit|...",
  "ssr": "next-pages|next-app|nuxt|remix|sveltekit|astro|null",
  "special": ["electron","extension","micro-frontend","webview"],
  "state": "redux|vuex|pinia|zustand|...",
  "comm": ["rest","graphql","ws","sse","postMessage"],
  "template_engine": "ejs|hbs|pug|njk|null",
  "ai_integration": false,
  "aliases": {"@/*":"src/*"},
  "monorepo": null,
  "api_routes": false,
  "inferred": false
}
```

- ai_integration: deps含openai/@anthropic-ai/@ai-sdk/langchain，或SSE+streaming+markdown渲染
- aliases: tsconfig paths / vite resolve.alias / webpack resolve.alias
- monorepo: 检测 workspaces → 仅对 **frontend_root** 对应子包读 package.json（计入 5 文件限制）；各 workspace 可独立 scope
- api_routes: 检测pages/api/ · app/api/ · server/api/ · routes/*.server · +server → 标记SSR-SSRF扫描
- **未读package.json → inferred:true + 报告头警告**

### 0.2 Search-first Sink 预扫

**范围：** 仅在 **frontend_root** 下执行；grep/搜索路径前缀为 frontend_root。

**IF grep/search工具可用：**
读取`references/rule-index.md` §grep-patterns → 拼装匹配 stack_profile 的模式子集 → **在 frontend_root 下**全目录搜索
- api_routes=true时追加§ssrf-patterns

**ELSE：**
在 **frontend_root** 下读文件树 → 按扩展名+路径筛选 → 标注`[扫描:手动枚举]`

**Shard过滤（命中>80时启动）：**
1. 同目录>5命中 → 采样2个 + 目录统计
2. 优先保留：innerHTML/v-html/dangerouslySetInnerHTML · 路径含auth/payment/admin/user/chat · 路由入口 · API routes
3. 降优先：components/ui/ · components/common/ · layouts/

**快速退出（命中=0且凭证=0时）：**
```
IF stack_profile.ssr != null THEN
  补充扫描SSR数据函数(getServerSideProps|useAsyncData|useFetch|loader等)
  IF 命中>0 THEN 正常进入Phase 1
IF 仍无命中 THEN 快速退出：仅CSP/CORS/Cookie/供应链 → 精简报告
```

### 0.3 分片计划（Shard Mode）

**范围：** 分片路径均相对于 **frontend_root**。

热区聚类（路径启发式）：
1. 同一 frontend_root 下的 src/modules/X/ 或 src/pages/X/ 等路径的命中 → 一个热区
2. 路由入口为热区锚点，其引用组件归入同热区
3. 全局共享文件(utils/store/api) → 按被引用最多的热区分配；若被≥3个热区引用 → 独立Shard标注[shared]
4. API routes → 独立Shard或归入对应业务热区
5. Phase 1 追踪后发现跨热区依赖 → 允许合并

```
## 分片计划
- Shard 1 [P0]: src/modules/payment/** — 8 Sink, ≈12 files
- Shard 2 [P0]: src/modules/auth/** — 5 Sink, ≈8 files
- Shard 3 [P1]: src/components/Chat/** — 3 Sink, AI streaming
- Shard 4 [shared]: src/utils/** — 被Shard 1,2,3引用
- Shard 5+: [列表] — 按需触发
- 未覆盖高风险: src/legacy/** — 45 Sink（建议后续审计）
```

### 0.4 自检 + 输出 → `recon-profile`

**Phase 0 自检：**
- [ ] **frontend_root** 已由 0.0 自动确定并写入 recon-profile
- [ ] package.json 已读取？（否→inferred:true 已标记？）
- [ ] 检测到的stack所有对应grep模式已执行？
- [ ] 每组grep至少列出1条原始命中行作为证据？（0命中需显式标注`[0 hits]`）
- [ ] 分片计划覆盖全部P0/P1 Sink？
- [ ] 未覆盖高风险区域已列出？

含：**frontend_root** + stack_profile + sink_hits + shard_plan + 扫描方式 + 自检结果。**不输出到对话**；写入工作文件（若可用）后直接进入 Phase 1 Shard 1。

---

## PHASE 1: SCAN（按分片执行，每片独立，每turn单片）

读取recon-profile获取当前分片信息。

### 1.0 AST-Lite Import感知

对当前分片Sink命中文件，读取头部import/require区域（≤20行/文件，不计入行预算）→ 构建该分片局部依赖子图 → 指导跨文件追踪。

### 1.1 JIT规则加载

读取 `references/rule-index.md` §route-table → 遇具体 Sink/场景时按需加载对应 reference（路径均为 `references/` 下同名文件）。
常识 Sink（innerHTML / eval / v-html / dangerouslySetInnerHTML / document.write）内置知识，不查阅。

### 1.2 Sink-first扫描

加载`references/scan-strategy.md` → 按Sink-first流程执行扫描。

### 1.3 自检 + 输出 → 追加`todo-list`

**Phase 1 自检（每Shard）：**
- [ ] 本Shard全部grep命中已访问？（noise已过滤？）
- [ ] noise + TODO = 本Shard grep命中总数？
- [ ] 无未标[✓]或[?]的文件引用？
- [ ] 无未读取即引用的函数/变量？
- [ ] 预算使用量（行/文件/TODO）

```
## Shard 1 — YYYY-MM-DD
| # | Pri | 文件→组件 | Sink | 上下文 | Source | 信任 | 证据 | TRACE | status |
|---|-----|----------|------|--------|--------|------|------|-------|--------|
| T-001 | P0 | [✓]Comment.vue→tmpl | v-html="comment.content" | html_body | API(评论) | 🟡 | E1 | api.ts→[d]store→Comment.vue | pending |
| T-002 | P1 | [✓]config.js→exports | AKIA... | credential | 硬编码 | 🔴 | E1 | — | pending |
```

P2-P5仅摘要行。超限→P0→P5截断，余项记入「未扫描Sink清单」。**不输出到对话**；将 todo-list 写入工作文件或内部保持后，若有未扫描分片则进入下一 Shard，否则进入 Cross-Shard 对账，再进入 Phase 2。

---

## CROSS-SHARD RECONCILIATION（所有分片Phase 1完成后）

**对话模式（中间不输出）：**
```
跨分片对账所需 todo-list 从工作文件或本对话上下文（内部保持）读取；不向用户请求粘贴。
若无法汇总（如无文件写入且早期 Shard 已滚出上下文）→ 在内部尽可能合并已有信息后继续，跨 Shard 链路标⚪待确认；仍不输出中间内容。
对账完成后直接进入 Phase 2，不输出「跨分片对账完成」等提示。
```

**正常流程：**
```
1. 汇总所有Shard的todo-list
2. 识别跨Shard数据流：
   - Shard A的Source来自Shard B的TODO中的同一API/store → 标注[cross-shard:A→B]
   - [shared]Shard中的util被多Shard引用 → 确认util TODO影响范围 → 复制到受影响Shard
3. 合并逻辑：跨Shard依赖链路可合并为单条TODO（取终端Sink所在Shard）
4. 更新todo-list
```
**不输出到对话**；对账完成后直接进入 Phase 2。

---

## PHASE 2: VERIFY（按片验证，每批5-8个TODO，每turn单片）

### 2.0 加载决策树

读取`references/verify-decision-tree.md` → 获取判定卡格式 + 完整决策流程(Step 1-3) + 严重性/证据模型 + 净化缓存规则。

### 2.1 批次执行

读取todo-list当前分片pending项。按决策树逐条验证：

```
FOR 每条pending TODO:
  IF E3 → §E3快速升级（仅P0）
  IF E1/E2 → 内部填写判定卡(Step 1→2→3)，不输出到对话
  → 更新 status（confirmed/excluded/pending）
```
**判定卡仅内部使用，不向用户展示**；仅在生成最终报告时汇总为报告中的漏洞条目。

场景专项按需加载reference（见决策树§场景路由）。

### 2.2 状态更新

每验证一条 → 更新todo-list该条status：`confirmed` / `excluded` / `pending`

排除记录：`| T-005 | excluded | Step1 | Source为硬编码枚举 |`

### 2.3 自检 + 报告

**Phase 2 自检（每批）：**
- [ ] 每条E1/E2已输出完整判定卡？
- [ ] confirmed + excluded + pending = 本批总数？
- [ ] 每条excluded有Step+原因？
- [ ] 净化缓存条目含Sink上下文？

**F0全局自检（最终报告前）：**
- [ ] 全部TODO: confirmed + excluded + pending = 总数？
- [ ] 所有V-### 有fingerprint？
- [ ] 局限性声明已包含？
- [ ] 未覆盖区域已列出？

报告格式按`references/rule-index.md` §report-template 输出 → 写入 **frontend_root** 下的 `security-audit-report-YYYYMMDD.md`；若文件写入不可用则完整报告输出到对话。

**→ 此时才向用户输出**：将上述报告作为**唯一**展示给用户的内容（文件路径 + 若在对话中则贴出报告全文或摘要）。不输出「Shard X 验证完成」等中间提示；全部完成后仅输出最终报告。

---

## DIFF MODE 工作流（audit_mode=diff）

```
1. 读取diff文件列表（git diff / 用户提供）
2. 对变更文件执行grep → 识别Sink
3. 追踪每个Sink的deps(≤2层) + 反向引用方(谁调用了变更函数)
   - 反向引用方>10 → 仅保留含P0/P1 Sink的调用方(≤5个)
   - 仍>5 → 按路径优先级(auth>payment>admin>api>其他)取Top 5
   - 余项记入「未审计引用方清单」
4. 反向引用方含Sink → 纳入TODO
5. Phase 1/2正常执行，scope限定在Δ+deps+反向引用方
```

---

## 执行边界

| 维度 | fast | deep | diff |
|------|------|------|------|
| 文件/片 | ≤10 | ≤15 | Δ+deps |
| 行数/片 | ≤800 | ≤2000 | ≤800 |
| TODO/片 | 15 | 30 | 15 |
| 验证/批 | 8 | 8 | 8 |
| 追踪深度 | 1 | 至确认Source或8层 | 2 |

**预算自适应（上下文紧张时）：**
1. 当前文件内grep命中≥4个Sink → 视窗压缩至±25行
2. 已用行数>80%预算且P0/P1未完 → P3+延后至下批
3. 已用行数>90% → 仅P0继续，余项记入「未扫描清单」
4. P4/P5自动归⚪待确认
5. TRACE 压缩单行
6. **自动进入下一分片**（无需用户说「继续」）

**@audit-safe处理：** `// @audit-safe: 原因` — 原因充分 → **降至P5**（不跳过）；原因不充分 → 保持原优先级+标注"@audit-safe理由不充分"。禁止完全跳过。

---

## 后续指令

修复V-001 → 加载references/fix-strategies.md · V-002为误报 → 排除 · 扩展U-001 → 读取建议文件 · 继续Shard N · 导出JSON · 对比历史(需提供审计状态摘要,按fingerprint对比) · OWASP分类
