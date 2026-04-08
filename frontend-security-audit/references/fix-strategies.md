# 修复策略 — v6

> 仅include_fix或用户请求时加载。优先已有依赖。

## 原则
1. **结构性消除**（最优）：textContent/框架文本绑定({{ }}/{ })/Trusted Types
2. **成熟净化**（次选）：DOMPurify/sanitize-html/isomorphic-dompurify(SSR)
3. **最近净化**：Sink前最近位置，净化后不再拼接

## 按上下文

| 上下文 | 修复 |
|--------|------|
| HTML body | textContent/{{}}；需HTML→DOMPurify(严格配置)；SSR→isomorphic-dompurify |
| attr(src/href) | new URL()→protocol白名单(https/http)→hostname白名单→拒javascript:/data: |
| attr(on*) | 禁动态绑定；事件用addEventListener+固定handler |
| attr(style) | 禁用户输入；必须→CSS.escape()每个属性值 |
| URL导航 | new URL→protocol(https/http)+hostname白名单→拒javascript:/data:；优先相对路径 |
| JS执行 | 消除eval→JSON.parse/Map/函数引用；setTimeout/setInterval传函数引用非字符串 |
| CSS | CSS.escape()；禁url()/expression()/@import含用户输入 |
| Server fetch(SSRF) | URL白名单(协议+域名)；禁内网IP段(含IPv6)；DNS解析后验证IP；禁自动跟随重定向或每跳验证 |

## 按类型

| 类型 | 修复 |
|------|------|
| 凭证 | 环境变量/密钥管理服务(Vault/AWS Secrets Manager)；前端仅通过后端代理访问 |
| postMessage | origin严格===匹配+event.source验证+data结构/类型校验+DOM操作用textContent |
| 重定向 | 服务端白名单校验；前端仅允许相对路径；new URL验证同源 |
| SSR序列化 | serialize-javascript(含自动`</`转义)；或devalue/superjson |
| 原型污染 | 过滤__proto__/constructor/prototype键(递归)；Object.create(null)作目标；Object.freeze原型 |
| CSRF | SameSite=Strict/Lax + CSRF token(服务端验证) + 自定义header(X-Requested-With) |
| 供应链 | 精确版本(无^/~)；提交lockfile；@scope:registry=私有；SRI所有CDN脚本 |
| AI输出 | DOMPurify.sanitize()每chunk；禁innerHTML+=→用textContent或净化后insertAdjacentHTML；Markdown关闭raw HTML(rehype-sanitize替代rehype-raw) |
| OAuth | authorization code+PKCE(S256)；token存HttpOnly cookie或内存(非localStorage)；state+nonce(crypto随机)；redirect_uri严格全匹配 |
| CSS-in-JS | CSS.escape()每个动态值；禁url()/expression()含用户输入；Tailwind禁arbitrary value含用户输入 |
| Clickjacking | X-Frame-Options: DENY + CSP frame-ancestors 'none'(或指定域) |
| Content-Type | X-Content-Type-Options: nosniff(所有响应) |
| CSWSH | WebSocket握手验证Origin + 连接ticket/token(非仅Cookie) |
| WebRTC | iceTransportPolicy:'relay'(需要时) + 自建TURN服务器 |
| GraphQL | graphql-depth-limit + graphql-cost-analysis/graphql-rate-limit + 批量查询限制 + 生产禁introspection + persisted queries |
| 竞态条件 | 前端：请求去重/debounce/loading状态锁；后端：幂等key/乐观锁 |
| 弱随机 | crypto.getRandomValues()/crypto.randomUUID()替代Math.random() |
| DOM Clobbering | 避免裸全局变量；getElementById后typeof检查；DOMPurify配置SANITIZE_NAMED_PROPS |
