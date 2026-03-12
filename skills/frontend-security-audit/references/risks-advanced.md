# 高级风险 §3-§16 — v6

**§3 DOM Clobbering：** 裸全局变量+用户可注入HTML(如DOMPurify默认允许id/name) · getElementById/getElementsByName未类型检查(访问.toString/.valueOf) · 表单name覆盖(document.forms) · 链式clobbering(a.b通过`<form id=a><img name=b>`)

**§4 供应链攻击：** Dependency Confusion公共registry抢注→.npmrc scope+占位包 · lockfile注入resolved变更→人工确认 · postinstall脚本含网络/shell

**§5 OAuth/OIDC：** state缺失/可预测 · implicit flow(token in URL) · redirect_uri非严格(子路径/通配) · token存localStorage(XSS可窃取) · nonce缺失 · PKCE未用/非S256 · ID Token未验证aud/iss/exp

**§6 Web Crypto：** AES-ECB(无IV,模式泄露) · IV硬编码/全零 · SHA-1完整性(碰撞) · PBKDF2<100k(暴力) · 密钥存localStorage/源码 · RSA<2048 · 无HMAC完整性校验

**§7 WASM：** 动态URL加载(fetch可控URL→instantiate) · importObject暴露eval/Function/DOM操作 · 缺wasm-unsafe-eval CSP · WASM内存越界读(信息泄露)

**§8 微前端：** 共享window无沙箱(qiankun/single-spa) · 跨应用postMessage未验证origin · 共享状态(Redux/全局变量)未授权写入 · 子应用props含敏感数据 · 子资源不受主应用CSP约束 · CSS污染(全局样式覆盖子应用布局→UI欺骗)

**§9 WebView(混合应用)：** bridge参数可控+Native未校验 → 命令注入 · 过多Native能力暴露(文件/相机/通讯录) · URL scheme未验证origin · evaluateJavascript(可控)=eval · 共享cookie/storage · Universal Links/App Links劫持

**§10 Mutation XSS：** 自制净化+innerHTML(浏览器解析与净化器不同→绕过) · 净化后二次DOM操作(cloneNode/adoptNode/Range) · DOMPurify非最新/ALLOWED_TAGS含style+事件 · 嵌套math/svg/foreignObject(命名空间混淆)

**§11 原型污染→XSS：** _.merge/deepmerge/$.extend/Object.assign用户可控输入(API body/query/JSON) · 未过滤__proto__/constructor/prototype · 下游污染对象属性→DOM Sink(如config.innerHTML/template) · gadget链：Object.prototype.innerHTML/src/href被框架读取

**§12 CSS-in-JS：** css`/styled.div`含可控变量 → CSS注入 · 动态style含url()→数据外泄 · expression()(IE遗留) · @import(外域) · styled-components attrs()可控 · Tailwind arbitrary values`[用户输入]`

**§13 GraphQL安全：**
- 生产环境开启introspection → 信息泄露(🔵)
- 无查询深度限制(graphql-depth-limit) → 嵌套查询DoS(🟡)
- 无查询成本分析 → 批量/宽查询DoS
- 批量查询(batching)：单请求[{q1},{q2},...{qN}]绕过rate limit → 无批量限制=🟡
- 用户字段(bio/comment/displayName)直达DOM无净化 → XSS(按Sink判定)
- Mutation输入未验证 → 结合存储型XSS
- Subscription(WebSocket)同§14

**§14 WebSocket安全：**
- CSWSH：握手无Origin验证+Cookie认证 → 跨站劫持(🟡,需后端确认)
- 消息注入：server推送用户可控内容→DOM无净化 → XSS
- 认证：仅Cookie无ticket/token → 配合CSWSH
- 重连逻辑：自动重连URL可控 → 中间人
- 消息格式：JSON.parse无try-catch → DoS · 自定义协议缺类型校验

**§15 WebRTC安全：**
- ICE candidate泄露内网IP(🔵,现代浏览器mDNS缓解,授予媒体权限后仍可能泄露)
- SRTP密钥交换：DTLS证书未验证 → 中间人(⚪需后端确认)
- DataChannel：onmessage内容→DOM → 同XSS Sink
- 信令服务器(通常WebSocket) → 同§14

**§16 前端竞态条件(Race Condition)：** （附录级别，条件苛刻，标⚪+需后端确认）
- TOCTOU：检查权限→await异步操作→执行(权限可能已变) → ⚪+需后端确认
- 并发请求：同一操作多次触发(按钮防抖缺失+服务端无幂等) → 🔵
- 异步状态不一致：await间隙state被其他事件修改 → 导致安全检查被绕过（JavaScript单线程，仅await处可中断）
