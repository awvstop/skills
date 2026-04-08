# SSRF / File / GraphQL / gRPC / Protocol / Crypto — BSAF v3.6

> 网络面漏洞。自包含。

## SSRF

**Sink**：fetch/axios/got/request/requests/httpx/node-fetch + 用户可控 URL。
**验证**：协议+域名白名单、禁内网 IP(含 IPv6/云 metadata)、DNS 解析后二次校验(防 DNS Rebinding)、禁跟随重定向。
云部署+SSRF → 🔴。内部服务(localhost/.svc.cluster.local/:6379等) → 🔴。
**URL 构造传播**：new URL(req.body.url)/url.parse → 追踪到最终 HTTP 调用。
**渲染 SSRF**：puppeteer/playwright/wkhtmltopdf + 用户可控 URL → 🔴。未禁 file:// 或 --no-sandbox+root → 🔴。
**Java Sink**：RestTemplate / WebClient / URL.openConnection() / OkHttpClient / Apache HttpClient / Jsoup.connect → 详见 frameworks-java.md。

**SSRF 变种**：
- **重定向链枚举内网**：服务端跟随重定向 → 攻击者控制域名首次响应 301→内网 IP → 绕过基于主机名的白名单 🔴；防护：禁止跟随重定向或重定向后重新校验目标
- **URL 解析不一致**：URL 校验库与 HTTP 客户端库解析不同（如 `new URL()` vs `fetch()` 对 `http://evil.com@internal.host/` 的处理）→ 绕过白名单 🔴；防护：统一用同一库解析后再传递
- **unix:// socket SSRF**（Linux）：`unix:///var/run/docker.sock` → 控制 Docker 🔴；防护：协议白名单在 scheme 层阻断

**危险 URL 协议**（协议白名单仅允许 http/https 不够）：
- `file://` → 读本地文件 🔴
- `gopher://` → 原始 TCP 注入（Redis `FLUSHALL`/内网 HTTP 请求）🔴
- `dict://` → Redis/Memcached 命令执行 🔴
- `ftp://` → FTP 端口探测/数据传输 🟠
- `ldap://` / `ldaps://` → LDAP 注入/JNDI 链 🔴
- `jar://` → Java Jar:// SSRF 读取任意文件 🔴
- **防护**：协议白名单 `['http','https']` + URL scheme 检查（`url.protocol`）在 DNS 解析前执行

**DNS Rebinding**：
- 攻击者域名首次解析 = 合法 IP（通过白名单），TTL 极短后解析 = 内网 IP → 绕过基于域名的白名单 🔴
- **防护**：DNS 解析后对 IP 二次校验（私有地址范围）：`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `::1`, `fd00::/8`；禁止跟随重定向后再次 resolve

## 路径遍历

path.resolve(base,input)+startsWith(base)+禁../ → ✅。path.join 无 resolve → 不充分。  
**Zip Slip**：解压前校验 entry resolve 后在目标内。

### 开放重定向（Java）

| Sink | 风险 |
|------|------|
| `return "redirect:" + request.getParameter("url")` | 🔴 |
| `new RedirectView(userInput)` | 🔴 |
| `HttpServletResponse.sendRedirect(userInput)` | 🔴 |
| `new ModelAndView("redirect:" + userInput)` | 🔴 |

须白名单或固定目标。详见 frameworks-java.md Spring MVC「开放重定向」。

## 文件上传

类型白名单+magic bytes、随机文件名、隔离目录、大小+数量限制。类型+路径同时缺失 → 🔴。
multer originalname 未净化 → 路径遍历。formidable keepExtensions:true → 危险。busboy 无大小限制 → 🟡。

**文件类型混淆**（上传后以错误 Content-Type 提供服务）：
- SVG 上传 → 服务端以 `image/svg+xml` 提供 → SVG 含 `<script>` → Stored XSS 🔴
- HTML 上传 → `text/html` 提供 → 任意 XSS 🔴
- JPEG 文件头 + HTML body（Polyglot）→ 某些浏览器执行 🟠
- PDF 含 JavaScript → 部分浏览器执行 🟡
- **防护**：用户上传文件下载时强制 `Content-Disposition: attachment`；禁止 `Content-Type: text/html`/`image/svg+xml` 提供用户上传内容；静态资源域与主域隔离（不同 origin）

## GraphQL

Spring GraphQL 同样适用该段（depth/cost/batch/introspection）。  
- Introspection 生产禁用
- depthLimit + costAnalysis + 字段级授权；无限制 → 🟡
- 敏感字段(passwordHash/internalNotes) 暴露 → 🟠/🔴
- resolver args.id 无 context.user → BOLA
- 嵌套 resolver 未独立校验 → N+1 授权缺失 🟡
- mutation 无独立 rate limit → 🟡
- **Alias 爆炸**：单 request 多别名绕过 rate limit → 🟡
- **循环 Fragment**：无深度检测 → 🟡
- **Array Batching**：[{query:...},{query:...}] 绕过限流→ 🟡；金融 → 🔴
- **Subscription**：无连接认证 → 🔴；无订阅级权限 → 🟡

## WebSocket

连接级认证 → 无 🔴。消息 schema 校验、频率限制、token 过期断开。

### Spring WebSocket STOMP

`@MessageMapping` / `@SubscribeMapping` = 入口点。须检查：`registerStompEndpoints().setAllowedOrigins("*")` → 🔴；无 `configureClientInboundChannel` 认证拦截器 → 🔴；`@Payload` 无 `@Valid` → 🟡；SimpleBroker/StompBrokerRelay 认证与凭证。详见 frameworks-java.md「Spring WebSocket STOMP」。

## gRPC

无 TLS(plaintext) → 🟡/🔴。metadata 认证、拦截器覆盖。反射生产关闭。

## 不安全随机性

Math.random/random.random 用于 token/session/nonce/OTP → 🔴。Date.now()/uuid.v1 用于不可猜测 ID → 🔴/🟡。

## 弱加密

MD5/SHA1 密码哈希 → 🔴。DES/RC4/ECB → 🔴。createCipher(无iv)、硬编码 IV → 🟡。

## 时间侧信道

=== 比较 secret/token → 🟡。timingSafeEqual/compare_digest → ✅。bcrypt.compare 自带恒定时间 → 排除。

**Java 特化**：`MessageDigest.isEqual(a, b)` → ✅（Java 6u17+ 恒定时间）；`Arrays.equals(a, b)` → ✅；`String.equals(secret)` → 🟡（JIT 优化可能短路）；`==` 比较 byte[] → 🟡。

## TLS/证书

rejectUnauthorized:false/verify=False/NODE_TLS_REJECT_UNAUTHORIZED=0 → 🔴(生产)/🟡(仅dev)。  
密钥文件(.pem/.key/.p12/.pfx/.jks)提交仓库 → 🔴。硬编码 JWT secret 无轮换 → 🟡。

## HTTP Host Header 注入

**Sink**：用 `Host` / `X-Forwarded-Host` / `X-Forwarded-Proto` 构造绝对 URL。
- 密码重置链接：`resetLink = req.headers.host + '/reset?token=' + tok` → 攻击者控 Host → 邮件含恶意域 🔴
- 缓存 key 含 Host → 缓存投毒（不同用户看到同一 Host 的缓存页）🔴
- **防护**：BASE_URL 固定于 env/配置；禁用 Host header 构造绝对 URL；如需信任 XFH，校验其在白名单内

## Web Cache Poisoning / Deception

**Cache Poisoning**：
- 未键入(unkeyed) 输入影响响应：`X-Forwarded-Host` / `X-Original-URL` / `X-Rewrite-URL` 影响 JS 路径/重定向但不含在 cache key → 投毒 🔴
- 检查：Vary 响应头是否覆盖实际影响响应的头；CDN/反代 cache key 配置
- **修复**：将实际影响响应的头加入 `Vary`（如 `Vary: X-Forwarded-Host, Accept-Encoding`）；或在 CDN 配置中明确 cache key 包含这些头；敏感响应加 `Cache-Control: private, no-store`

**Cache Deception**：
- `/api/user/profile` 无 `Cache-Control: no-store` + CDN 按路径缓存 → 攻击者构造 `/api/user/profile/foo.css` → CDN 缓存私有响应 → 跨用户读取 🔴
- 敏感 API 端点缺 `Cache-Control: private, no-store` → 🟡

## Padding Oracle

AES-CBC 解密时：padding error 与 MAC error 返回不同状态码/响应时间/消息 → oracle 攻击 → 任意解密/伪造密文 🔴。
**防护**：改用 AEAD（AES-GCM）；错误统一响应；恒定时间处理（MAC-then-Encrypt→Encrypt-then-MAC）。
**检查**：加密 cookie、encrypted token、加密 querystring 参数；CBC 模式使用场景。

## 解压炸弹（Decompression Bomb）

zip/tar/gz/brotli 解压前未检查解压后大小 → 内存/磁盘耗尽 DoS 🟡（大型生产系统 → 🔴）。
- Node：`node-tar` / `adm-zip` / `yauzl` → 逐条校验 `header.size`，累计大小上限
- Python：`zipfile.ZipFile` → 先读 `namelist()` 检查每条 `file_size`；`tarfile` 同理
- Java：`ZipInputStream` 检查 `getSize()` / 累计解压字节；`commons-compress` 同
- 防护：解压大小上限（如 50MB）+ 文件数量上限 + 单文件大小上限

## 符号链接攻击

解压 tar/zip 含 symlink 条目（`../../../etc/passwd`）→ 路径逃逸 → 读/写系统文件 🔴。
- 检查：解压前校验 entry 是否为 symlink（`entry.isSymbolicLink()`）；如需允许，校验 realpath 在目标目录内
- Java：`ZipEntry.isDirectory()` 不够；须检查 `Files.isSymbolicLink()`；commons-compress `TarArchiveEntry.isSymbolicLink()`
- Node：`yauzl`/`adm-zip` 默认不检查 symlink；须手动过滤

## HTTP Client 全局配置风险

HTTP 客户端的全局/默认配置被用户可控值污染 → 影响所有后续请求：

- **axios.defaults.baseURL = userInput**：后续 `axios.get('/api/data')` 实际请求攻击者服务器 → SSRF/凭证泄露 🔴
- **axios.defaults.headers['Authorization'] = userToken**：全局 header 在多租户场景泄露 → 🔴
- **requests.Session()**：Python Session 设置 `session.headers.update({'X-API-Key': userInput})` → 凭证伪造 🟠
- **RestTemplateBuilder.rootUri(userInput)**：Java Spring 全局 base URL 可控 → SSRF 🔴
- **WebClient.baseUrl(userInput)**：同上 🔴
- **got.extend({prefixUrl: userInput})**：Node got 全局 prefix 可控 → SSRF 🔴
- **检查**：HTTP client 初始化代码（单例/全局实例）；构造参数是否来自 🔴/🟠 Source

## HTTP/2 特有攻击

**CVE-2023-44487 Rapid Reset（DoS）**：
- 客户端高速发送 HEADERS 帧后立即发送 RST_STREAM → 服务端新建流但立即取消 → CPU/内存耗尽 🔴
- 检查：服务端是否有 HTTP/2 连接速率限制/流数限制（Nginx `http2_max_concurrent_streams`、Java Netty `maxConcurrentStreams`）
- 受影响：所有 HTTP/2 服务端（Nginx/Apache/Netty/Node http2 module）；已修复：Nginx ≥ 1.25.3、Netty ≥ 4.1.100

**:authority 伪头注入**：
- HTTP/2 请求中 `:authority` 伪头相当于 Host 头；服务端若用 `:authority` 构造 URL 但未白名单校验 → Host Header 注入 🔴
- 检查：后端框架将 HTTP/2 `:authority` 映射到 `Host` 是否一致；同 HTTP Host Header 注入检查

**HPACK 压缩侧信道**：
- 响应包含攻击者可观察的压缩比 → 推断敏感 header 值（CRIME 类攻击）🟡
- 检查：HTTPS 下 header 是否含 CSRF token / session id 等敏感值；通常框架层已缓解

## HTTP Request Smuggling / CRLF

- 反向代理+Node/Python → CL.TE/TE.CL desync → 🟡；确认 → 🔴。建议 smuggler 工具验证。
- 响应头用户输入未过滤 \r\n → CRLF 🟡/🔴。

## SSE

认证、来源校验、敏感数据过滤、连接数限制。无认证 → 🟡。

### 嵌入式服务器安全配置（Java）

server.tomcat.relaxed-path-chars → 路径绕过向量 🟡。Undertow allow-encoded-slash=true → 🟡。Jetty sendServerVersion=true → 🔵。详见 frameworks-java.md「嵌入式服务器安全配置」。
