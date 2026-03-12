# 验证条件矩阵 — v6

> 全部满足才算充分。

| 场景 | 条件 |
|------|------|
| postMessage | origin严格白名单(非*)+source验证+data类型校验+DOM净化 |
| URL跳转 | 协议白名单(https/http)+域名严格匹配+new URL()解析(非正则) |
| DOM操作 | 成熟净化库+严格配置+Sink前+未覆写+未二次拼接 |
| 代码执行 | 禁用户输入+沙箱 |
| 正则校验 | ^$+.转义+已知绕过测试+非ReDoS |
| iframe | sandbox合理+scripts与same-origin不同时+allow-*最小化 |
| 硬编码凭证 | 非占位+生产路径+非模板 |
| 开放重定向 | 协议+域名+不仅正则+服务端验证 |
| SSR序列化 | 安全序列化库(serialize-javascript/devalue/superjson)+转义`</` |
| AI输出 | AI=🔴+渲染前净化+streaming中途每chunk净化+禁innerHTML+= |
| OAuth/OIDC | state+nonce+PKCE(S256)+token不存localStorage+redirect_uri严格匹配 |
| 深合并 | 过滤__proto__/constructor/prototype+输入非可控 |
| CSS-in-JS | CSS转义(CSS.escape)+禁url()/expression()+禁用户控制选择器 |
| 流式渲染 | 每chunk净化+禁innerHTML+=+完整标签边界处理 |
| Web Crypto | 非ECB+IV非硬编码+非SHA-1+PBKDF2≥100k+密钥非硬编码 |
| SSRF(SSR) | URL协议白名单(https)+域名/IP白名单+禁内网IP(10./172.16-31./192.168./127./169.254./::1/::ffff:127.0.0.1/fc00::/fd00::)+DNS解析后二次验证IP+禁重定向跟随或校验每跳 |
| GraphQL | 深度限制+成本分析+批量查询限制+禁生产introspection+输入验证+用户字段输出净化 |
| WebSocket | Origin验证+认证ticket/token(非仅cookie)+消息类型校验+输出净化 |
| WebRTC | iceTransportPolicy:relay(需要时)+ICE candidate过滤内网IP |
