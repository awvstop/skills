# Phase 2 决策树 — v6

> Phase 2开始时加载。每条E1/E2 TODO必须输出判定卡，未填完禁止给出判定。

## 判定卡格式（必须输出）

```
| 字段 | 值 |
|------|-----|
| TODO# | T-001 |
| Sink | v-html="comment.content" |
| Sink上下文 | html_body |
| Source | API(comment.content) |
| 信任 | 🟡 indirect |
| Source可控论证 | 端点/comments → 用户提交评论内容,依据:端点语义 |
| confidence | high |
| Step2-现有防护 | 无 |
| Step2-所需防护 | HTML转义或DOM净化库 |
| Step2-匹配? | ❌无防护 |
| Step3-需要? | 否(Step2已判❌) |
| Step3-结果 | — |
| 判定 | ⚠️confirmed |
| 严重性 | 🔴 |
| 证据 | traced+exploitable |
| fingerprint | v-html.content::stored-xss::api-response |
```

**Step3有净化时的判定卡示例：**
```
| Step2-匹配? | ✅(DOMPurify) |
| Step3-需要? | 是 |
| Step3-1库可靠 | ✅ DOMPurify 3.x |
| Step3-2配置严格 | ✅ 默认配置 |
| Step3-3位置正确 | ✅ Sink前一行 |
| Step3-4路径覆盖 | ❌ else分支未净化 |
| Step3-5未覆写 | ✅ |
| Step3-结果 | ❌(Step3-4失败) |
| 判定 | ⚠️confirmed |
| 严重性 | 🟡 |
```

## §E3快速升级（仅P0 Sink）

```
IF Sink为P0级(innerHTML/v-html/eval/dangerouslySetInnerHTML/SSRF-fetch)
  AND 所在文件已在本批读取范围 THEN
  同函数/同组件内快速追踪(≤30行)
  确认Source → 升级E2/E1 → 输出判定卡
  无法确认 → ⚪待确认（无需判定卡）
其余E3 → 直接⚪待确认（无需判定卡）
```

## Step 1 — Source追踪 + 信任

每批开始重读相关文件（已在上下文中的跳过）。

| 信任 | 来源 | confidence上限 |
|------|------|---------------|
| 🔴 external | URL参数/postMessage/WebSocket/AI输出/window.name/document.referrer/WebRTC DataChannel | high |
| 🟠 user | 表单/文件上传/contenteditable/clipboard | high |
| 🟡 indirect | API响应(含用户内容)/CMS/i18n/GraphQL用户字段 | high(须论证可控)否则medium |
| 🟢 storage | localStorage/sessionStorage/cookie/indexedDB | high(须论证污染路径)否则medium |
| ⚪ internal | store/cache/computed(非终态) | **继续追踪到写入源** |

**追踪规则：**
- 每跳标注`[✓]`或`[inferred]`
- 含[inferred]节点 → confidence≤medium
- **结构性推断例外：** 端点名含comments/posts/messages/profiles + 响应直达HTML Sink → 可达high，标注"依据:端点语义"
- 不可控(固定值/枚举/常量/配置白名单) → **排除**
- 无法追踪(外部模块/无源码) → **⚪待确认**
- [cross-shard]项须加载源Shard的TRACE验证

**→ 确定信任+confidence后 → Step 2**

## Step 2 — 防护上下文匹配

| Sink上下文 | 所需防护 |
|-----------|---------|
| HTML body | HTML转义(实体编码)或DOM净化库(DOMPurify等) |
| HTML attr | 属性转义+引号包裹+协议校验(src/href) |
| URL/导航 | 协议白名单(https/http)+域名白名单+new URL()解析 |
| JavaScript | 禁止用户输入进入eval/Function/setTimeout(string) |
| CSS | CSS.escape()+禁url()/expression()/import |
| Server fetch(SSRF) | URL协议+域名/IP白名单+禁内网段+禁重定向跟随 |

**常见错配（直接判⚠️确认）：**

| 错误防护 | 上下文 | 原因 |
|----------|--------|------|
| encodeURIComponent | HTML body | URL编码≠HTML转义 |
| JSON.stringify | SSR `<script>` | 不转义`</script>` |
| replace("<","&lt;") | 任意HTML | 不完整(仅首个/缺其他字符) |
| URL正则缺^/$/.未转义 | URL校验 | 绕过(evil.com.example.com) |
| DOMPurify | URL协议 | 不校验javascript:/data: |
| encodeURI | HTML attr | 不转义引号/HTML字符 |
| validator.isURL | URL安全 | 不校验协议(javascript:可过) |
| _.escape | HTML attr(无引号) | 不转义反引号/空格 |
| strip_tags | 富文本 | 绕过(未闭合标签/属性注入) |
| 内网IP黑名单(仅字符串) | SSRF | DNS rebinding/IPv6(::1/::ffff:)/八进制(0177.0.0.1)/十进制IP绕过 |

**泛化规则：** IF 防护函数设计用途上下文 ≠ Sink实际上下文 THEN 不匹配 → ⚠️确认。

→ 不匹配 = ⚠️确认 / 匹配 → Step 3

## Step 3 — 净化质量（5项全过排除）

1. **库可靠：** DOMPurify/sanitize-html/isomorphic-dompurify/框架内置净化（非自制正则/replace）
2. **配置严格：** 不允许script/iframe/object/embed/on*/javascript:/data: · DOMPurify ALLOWED_TAGS非过宽 · ALLOW_ARIA_ATTR/ALLOW_DATA_ATTR评估
3. **位置正确：** Sink前最近位置净化 · 净化后未再拼接不可信数据（trim/toLowerCase/parseInt不计）
4. **路径全覆盖：** 所有分支/条件路径均经净化 · 默认分支/错误处理路径(catch/else/default)不漏
5. **未被覆写：** 净化后的值未被spread({...obj, content: raw})/Object.assign/_.merge覆盖

无净化 → ⚠️确认；任一项失败 → ⚠️确认 + 在判定卡标注失败项编号。

## 净化缓存

**key = sanitizer名 + 配置签名 + Sink上下文类型**

```
DOMPurify|default|html_body → ✅
DOMPurify|{ALLOWED_TAGS:[...]}|html_body → 须独立验证配置
DOMPurify|default|url → ❌(DOMPurify不校验URL协议)
```

同key配置已通过 → 仅验参数来源+位置(Step 3.3-3.5)，判定卡Step3-1/3-2标"缓存命中"。
每批输出末尾维护缓存表。IF文件写入可用THEN同步写入sanitizer-cache.md。

## 场景专项路由（按需加载 reference，路径均相对于 skill 根目录）

| 场景 | 加载 |
|------|------|
| postMessage/iframe/URL跳转 | references/checks-validation-matrix.md |
| SSR序列化/RSC | references/risks-ssr-ai.md §1 |
| AI输出/流式 | references/risks-ssr-ai.md §2 |
| SSRF(SSR) | references/checks-validation-matrix.md + references/sinks-sources.md §ssrf |
| GraphQL | references/risks-advanced.md §13 + references/checks-validation-matrix.md |
| WebSocket | references/risks-advanced.md §14 + references/checks-validation-matrix.md |
| OAuth/OIDC | references/risks-advanced.md §5 |
| 原型污染/DOM Clobbering | references/risks-advanced.md §11/§3 |
| CSS-in-JS | references/risks-advanced.md §12 |
| Mutation XSS | references/risks-advanced.md §10 |
| Electron IPC | references/framework-electron.md |
| 其他高级 | references/risks-advanced.md 对应§ |

## 反误判规则

1. 看到净化 → 必须完成Step 2(上下文匹配)+Step 3(质量验证)
2. 他处有净化 → 验证**当前执行路径**是否经过该净化
3. API响应 → 至少🟡，不可直接标🟢或排除
4. 注释掉的验证 = 无验证
5. 部分验证(如仅校验长度不校验内容) ≠ 充分验证
6. try-catch中的净化 → 验证catch分支是否安全(是否直接使用原始数据)
7. 框架默认转义 → 确认未被绕过(raw/v-html/dangerously/bypass等)

## 严重性判定

| 严重性 | 判定 |
|--------|------|
| 🔴高危 | 可控Source→Sink→无有效防护，可构造payload |
| 🟡中危 | 防护不充分/可绕过/需特定条件/Source可控性需论证 |
| 🔵低危 | 信息泄露/最佳实践缺失/条件苛刻/仅配置问题 |

## 严格证据模型（双维度交叉）

| 链路完整性 | 可利用性 | 允许最高 |
|-----------|---------|---------|
| traced | exploitable | ⚠️确认(≤high) |
| traced | conditional | ⚠️确认(≤medium) |
| inferred | exploitable | ⚠️确认(≤medium) |
| inferred | conditional | ⚪待确认 |
| sink-only | — | ⚪待确认 |

**特殊：** 业务逻辑类(仅前端校验/前端权限控制) → ⚪待确认 + "需后端确认"
