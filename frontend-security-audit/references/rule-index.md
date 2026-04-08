# 规则路由 + Grep + 报告模板 — v6

> Phase 0加载。常识Sink(innerHTML/eval/v-html/dangerouslySetInnerHTML/document.write)内置知识。

## §grep-patterns

### 通用
```
innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|setTimeout\(|setInterval\(|createContextualFragment|\.srcdoc|importScripts|location\.(href|assign|replace)|window\.open|\.cookie\s*=|postMessage|onmessage|addEventListener\(['"]message
```

### React
```
dangerouslySetInnerHTML|ref\.current\.innerHTML|__NEXT_DATA__|href=\{(?!['"]https?:)
```

### Vue
```
v-html|Vue\.compile|v-bind="\$attrs"|:href=|:src=|:style=|__NUXT__
```

### Angular
```
bypassSecurityTrust|\[innerHTML\]|\$sce\.trust|ng-bind-html|\$compile|\[routerLink\]|\[href\]
```

### Svelte/jQuery/Lit/Astro
```
\{@html|\.html\(|\$\(|unsafeHTML|set:html
```

### SSR/Streaming
```
JSON\.stringify.*script|serialize.*data|ReadableStream|EventSource|for await
```

### SSR数据函数（快速退出豁免）
```
getServerSideProps|getStaticProps|getInitialProps|useAsyncData|useFetch|loader\s*\(|load\s*\(
```

### §ssrf-patterns（api_routes=true时追加）
```
fetch\(.*\$|fetch\(.*req\.|fetch\(.*params|fetch\(.*query|axios\(.*\$|axios\.get\(.*req\.|got\(.*req\.|undici.*request\(.*req\.|http\.request\(.*req\.
```
适用范围：pages/api/ · app/api/ · server/ · routes/*.server · +server · api/*.ts

### GraphQL
```
introspection|__schema|__type|graphql\(|useQuery|useMutation|gql`|depthLimit|costAnalysis
```

### WebSocket
```
new WebSocket|\.onmessage|ws\.on\(['"]message|io\(|socket\.on
```

### 凭证
```
sk-[a-zA-Z0-9]{32}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z\-_]{35}|xox[bpoas]-|sk_live_[a-zA-Z0-9]{24}|pk_live_[a-zA-Z0-9]{24}|DefaultEndpointsProtocol|AC[a-f0-9]{32}|api[_-]?key\s*[:=]\s*['"]|secret[_-]?key\s*[:=]\s*['"]|_authToken
```

> JWT不在grep阶段扫描。Phase 1遇到硬编码JWT字符串字面量时按checks-credentials.md §jwt规则处理。

## §route-table

所有文件均位于本 skill 的 `references/` 目录下，从主 SKILL 加载时使用 `references/文件名`。

| 场景 | 文件 |
|------|------|
| 非常识Sink/Source | references/sinks-sources.md |
| React/Next/Remix | references/framework-react.md |
| Vue/Nuxt | references/framework-vue.md |
| Angular/AngularJS | references/framework-angular.md |
| Svelte/jQuery/Lit/Astro/SW | references/framework-misc.md |
| Electron/Extension | references/framework-electron.md |
| CSP/CORS/CSRF/Cookie/TT/Clickjacking | references/checks-mechanisms.md |
| 硬编码凭证 | references/checks-credentials.md |
| 供应链/正则/SRI | references/checks-supply-chain.md |
| 场景验证条件 | references/checks-validation-matrix.md |
| SSR注入/AI XSS | references/risks-ssr-ai.md |
| §3-§16高级风险 | references/risks-advanced.md |
| Phase 1扫描操作规程 | references/scan-strategy.md |
| Phase 2决策树 | references/verify-decision-tree.md |
| 修复方案(include_fix) | references/fix-strategies.md |

## §report-template

**报告头（首片生成，后续更新）：**
```
## 安全审计报告
- 日期 | 模式 | 规则v6-YYYYMMDD
- 技术栈：{摘要}
- 审计深度：热区聚焦(N片) | 已审计Sink X / 预扫总数 Y
- 完整链路(E1) A | 推断链路(E2) B | 未追踪(E3) C
- 未审计高风险：[列表]
- 🔴A · 🟡B · 🔵C · ⚪D待确认
- confidence分布：high H · medium M
```

**已知局限（必须包含）：**
```
### 已知局限
1. 文本grep无法捕获：动态属性拼接·变量别名·装饰器/HOC包裹·运行时生成Sink
2. LLM上下文窗口限制跨文件追踪深度（硬限8层）
3. 仅静态分析，无运行时验证
4. 第三方库内部实现不审查（记录边界）
5. 业务逻辑漏洞需人工确认
6. @audit-safe标注仅降优先级，不保证安全
```

**🔴高危 — 完整格式：**
```
### V-001: 存储型XSS — 评论未净化渲染
**位置：** [✓]Comment.vue → template内div
**代码：** `<div v-html="comment.content"></div>`
**成因：** API响应comment.content(🟡,用户可提交→可控) → 无净化 → v-html(html_body)
**链路：** [✓]api/comment.ts →[dispatch] [✓]store/comments.ts →[read] [✓]Comment.vue | traced
**POC：** 入口:comment.content(代码:api/comment.ts→resp.data.content) · payload:`<img src=x onerror=alert(1)>` · ⚠️参数名来自已读取代码,需实际验证
**confidence:** high | traced+exploitable | **OWASP:** A03
```

**🟡🔵 — 压缩表格：**
`| 编号 | 级别 | 位置→组件 | 类型 | Sink | Source(信任) | confidence | OWASP | 利用条件 |`

**⚪待确认：**
`| 编号 | 位置→组件 | Sink | 截断原因 | 建议操作 |`

**附录：** 最佳实践(target="_blank"等)不计入统计

**审计状态摘要（增量审计用）：**
`V-001 | v-html.content::stored-xss::api-response | confirmed`

**JSON字段：** fingerprint · owasp · context · confidence · source_trust · evidence_level · trace_quality

**fingerprint：** `[SinkAPI].[属性]::[漏洞类型]::[Source类别]`
- innerHTML::reflected-xss::url-param · location.href::open-redirect::user-input · hardcoded::credential::hardcoded
- SSR隐式: getServerSideProps.return::ssr-injection::api-response
- SSRF: fetch.url::ssrf::user-input
- 原型污染→XSS: _.merge::prototype-pollution-xss::user-input
- 多Sink复合: 取链路终端Sink · 循环同Sink同Source → 合并
- 凭证Source类别固定hardcoded，不含前缀值

**OWASP映射：** XSS/注入→A03 · SSRF→A10 · 凭证→A07 · CSRF/CORS/权限→A01 · 供应链→A06 · 弱加密→A02 · 业务→A04 · 配置→A05 · 不明确→null

**无漏洞：** ✅ 未发现明显前端安全漏洞。（含局限性声明）

**后续交互：** 修复V-001 → 加载fix-strategies.md · 误报 → 排除 · 扩展 → 读取建议文件 · 继续Shard N · 导出JSON · 对比历史 · OWASP分类
