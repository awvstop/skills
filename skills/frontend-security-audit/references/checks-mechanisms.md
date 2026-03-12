# CSP / CORS / CSRF / Cookie / TT / Clickjacking / Headers — v6

**CSP：** unsafe-inline/unsafe-eval/data:/blob: · 白名单含JSONP/上传点/CDN通配 · nonce/hash未正确 · report-uri配置 · base-uri缺失

**CSRF：** SameSite + CSRF token/自定义header · 状态变更操作用GET → 🔴

**CORS：** Allow-Origin:*+敏感操作 · Credentials:true+宽松Origin · Origin反射(回显请求Origin) · 正则匹配Origin不严格

**Trusted Types：** createPolicy回调净化充分性 · 宽松default policy · require-trusted-types-for时重点policy审计 · 未强制时Sink扫描完整

**Sanitizer API：** setHTML()配置是否允许危险元素

**Cookie：** 缺HttpOnly/Secure/SameSite · token可JS读取 · Domain过宽 · Path不限定 · 过期时间过长

**弱随机：** Math.random()安全令牌/nonce · 时间戳作标识 · 可预测UUID(v1)

**原型链：** Object.assign/_.merge/$.extend(true)/deepmerge来自用户 · 未过滤__proto__/constructor/prototype

**信息泄露：** 生产sourceMappingURL · console.log敏感 · 错误堆栈暴露 · 注释中凭证/内部URL · window.__STATE__含敏感字段

**敏感API：** clipboard.readText()无提示 · Geo/Camera/Mic即时请求 · PaymentRequest参数可控

**Clickjacking：**
- 缺少X-Frame-Options header(DENY/SAMEORIGIN)
- 缺少CSP frame-ancestors指令
- 两者均无 → 🟡（敏感操作页面升🔴）
- 检查范围：登录/支付/设置/授权等关键页面

**Content-Type Sniffing：**
- 缺少X-Content-Type-Options: nosniff
- 上传/API响应未设Content-Type → 结合XSS可利用
- 🔵（仅配置缺失） / 🟡（结合上传点）

**CSWSH（Cross-Site WebSocket Hijacking）：**
- WebSocket握手未验证Origin header
- 无CSRF token/ticket机制
- Cookie自动附带 + SameSite=None → 可跨站劫持
- 检测：new WebSocket连接 → 追踪服务端Origin校验（前端无法确认→⚪待确认+"需后端确认"）

**WebRTC IP泄露：**
- RTCPeerConnection无STUN/TURN限制 → 泄露内网IP
- 未设iceTransportPolicy: 'relay'
- 现代浏览器(Chrome M87+)默认mDNS候选缓解，授予媒体权限后仍可能泄露
- 🔵（信息泄露）
