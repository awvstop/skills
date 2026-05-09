# Phase 0: RECON — 详细流程（不读源码正文）

> 骨架与触发条件见 SKILL.md；本文件为各子步骤的完整决策逻辑。

---

## 0.0 识别前端根目录（自动检测，无需用户指定）

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

---

## 0.1 技术栈识别（限读≤5文件，均在 frontend_root 下）

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

---

## 0.2 Search-first Sink 预扫

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

---

## 0.3 分片计划（Shard Mode）

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

---

## 0.4 自检 + 输出 → `recon-profile`

**Phase 0 自检：**
- [ ] **frontend_root** 已由 0.0 自动确定并写入 recon-profile
- [ ] package.json 已读取？（否→inferred:true 已标记？）
- [ ] 检测到的stack所有对应grep模式已执行？
- [ ] 每组grep至少列出1条原始命中行作为证据？（0命中需显式标注`[0 hits]`）
- [ ] 分片计划覆盖全部P0/P1 Sink？
- [ ] 未覆盖高风险区域已列出？

含：**frontend_root** + stack_profile + sink_hits + shard_plan + 扫描方式 + 自检结果。**不输出到对话**；在内部保持后直接进入 Phase 1 Shard 1。
