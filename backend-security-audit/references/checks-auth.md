# Auth / Access Control / Multi-tenancy — BSAF v3.6

> 认证、授权、BOLA、Mass Assignment、Session、OAuth、WebSocket、Webhook、多租户。自包含。

## 认证

- **路由覆盖率**：route_map 每条路由追踪中间件链。无认证+非公开路由 → Candidate。POST/PUT/DELETE/PATCH 无认证 → 🔴。
- **JWT**：algorithms 固定、禁 none、exp 检查、密钥来源(env✅/硬编码❌)。JKU/X5U 攻击者控 URL → 🔴。kid 路径遍历/SQL 注入 → 🔴。未验证 iss/aud → 🟡；微服务共用密钥+不验证 aud → 🔴。
- **Session**：Redis/DB 存储、regenerate、登出销毁、HttpOnly+Secure+SameSite(Lax/Strict)。SameSite=None 无 Secure → 🟡。Cookie 前缀 __Host-/__Secure-。
- **密码**：bcrypt/argon2✅；明文存储/日志 → 🔴。重置 token=CSPRNG+过期+单次。无复杂度策略 → 🟡。
- **MFA**：验证 API 无 rate limit → 🟡；可直接关闭无二次验证 → 🔴。
- **账户锁定绕过**：锁定/封禁用户已有 JWT/session 未失效 → 🟡。
- **API Key**：哈希存储、Header 传输、scope 限制。
- **Remember-Me**：Remember-me key 硬编码 → 可伪造 token 🔴。TokenBasedRememberMeServices 用 MD5 → 🟡。密码变更后 token 未失效 → 🟡。Remember-me 用于敏感操作无二次认证 → 🔴。详见 frameworks-java.md Spring Security「Remember-Me」。

## BOLA/IDOR

**三点对齐**：① 路由含资源 ID → ② DB 用该 ID → ③ 条件含 req.user.id。①②③ 满足 → ✅。①② 无 ③ → BOLA（🟡读/🔴写删）。

**加权**：自增整数+缺绑定 → 🔴；UUID+缺绑定 → 🟠（仍属漏洞，仅降低可遍历性）。  
**来源**：ID 从 req.body 取 → 🔴。GraphQL args.id 无 context.user 校验 → BOLA。  
**无参数 BOLA**：/api/me/profile 用 req.body.userId 而非 req.user.id → 🔴。  
**间接所有权**：用户→组织→资源须验证成员关系；委托关系须验证授权链。  
**复合路径**：/orgs/:orgId/projects/:projectId/tasks/:taskId → 三级绑定，任一缺失 → BOLA。  
**批量查询**：GET /api/tasks?projectId=xxx → 须校验 user 对 project 权限。  
**GraphQL 嵌套**：每级 resolver 须独立校验 context.user；仅顶级不够。  
**ID 字段启发式**：除 params.id 外检查 body.userId/accountId/orderId/orgId 等。

## 多租户隔离

- **租户 ID 来源**：仅从认证上下文(JWT/session)取 tenantId，禁止从 req.body/query 信任。
- **list/search/export**：强制带 tenant 过滤；分页/limit 限制。
- **批量操作**：按租户隔离。
- **scoped admin**：租户内 admin 无法访问其他租户。
- **Queue/Worker**：payload 含 tenant_id，consumer 按 tenant 过滤。
- **Cache**：key 含 tenantId，避免跨租户命中。
- **GraphQL/batch**：按租户隔离 resolver/loader。

**BOLA + 多租户**：须同时满足 ownership_binding + tenant_binding。无 tenant_binding → 不得 Confirmed，标 `[needs-tenant-context]`。

### Hibernate 原生多租户

CurrentTenantIdentifierResolver 从 request header/body 取 tenantId（非 SecurityContext）→ 🔴。Schema 隔离下 tenant identifier 可控 → 跨 schema 🔴。Discriminator 模式未在所有查询强制 @Filter → 🔴。

## Mass Assignment

Model.create/update(req.body)、Object.assign(entity,req.body) 无字段过滤 → 检查是否可写 role/isAdmin/balance。  
**安全**：显式 pick、DTO 白名单、fillable/guarded、ValidationPipe(whitelist:true)、Pydantic。

### 对象映射库绕过 DTO（Java）

BeanUtils.copyProperties(source, target) 无排除 → 映射 isAdmin/role 🟡。MapStruct @Mapper 默认全同名字段 → 🟡。ObjectMapper.convertValue(reqBody, Entity.class) → 🔴 绕过 DTO 白名单。详见 frameworks-java.md「对象映射库与 DTO 绕过」。

## 类型混淆 / 弱比较（认证绕过）

- **JavaScript `==` 弱比较**：`token == storedToken` 当两者均为 `undefined`/`null` → true → 绕过 🔴；`"0" == false` → true；`[1] == 1` → true。强制使用 `===`
- **JSON 类型注入**：`Content-Type: application/json` → `{"password": true}` → 若后端 `password == true` 弱比较 → 绕过 🔴；`{"role": ["admin"]}` 数组代替字符串绕过字符串校验 → 🟠
- **PHP 魔术哈希**（PHP 项目）：`md5("240610708") === "0e462097431906509019562988736854"` → `== "0e..."` 为 true → 🔴；密码/token 比较用 `hash_equals()`
- **Python `None` 比较**：token 从 DB 取出可能为 `None`；`if token == user_input` 且 user_input 可控为 `None`/`null` → 🟡
- **数字/字符串**：`userId: "1 OR 1=1"` 以字符串传入，后端 parseInt() 得 1 → 实际用了攻击者意图以外的值但不报错 → 须类型强验证

## Session Fixation

登录成功后未 regenerate session ID → 攻击者预植 session → 接管 🟠。
- Node：`req.session.regenerate()` 登录后调用
- Python Django：`request.session.cycle_key()` 或 `flush()+重建`
- Spring Security：`.sessionFixation().migrateSession()`（默认）或 `.newSession()`；`.none()` → 🔴

## JWT 算法混淆攻击

仅做 `algorithms: 固定` 不够；需防以下特定攻击：
- **alg=none 攻击**：`jwt.verify(token, key)` 未指定 algorithms → 签名绕过 🔴
- **RS256→HS256 混淆**：服务端接受 HS256 + 用 RS256 公钥作 HMAC secret → 攻击者用公钥伪造 token 🔴。防护：硬编码 `algorithms:['RS256']`，禁接受 HS256（非对称场景）
- **kid 注入**：`kid` 字段含路径遍历（`../../etc/passwd`）→ 以 null/空内容验签绕过 🔴；含 SQL 注入 → 任意密钥查询 🔴

## SAML 攻击（检测到 SAML 相关依赖时）

- **XML Signature Wrapping (XSW)**：签名节点被绕过，伪造 NameID/角色 → 身份冒充 🔴。防护：validateSignatureOnResponse 且验签覆盖整个 Response，勿仅验 Assertion
- **XXE in SAML**：XML 解析未禁外部实体 + SAMLResponse 含外部实体 → 🔴（同 XXE）
- **NameID 多值混淆**：解析器取最后/第一个 NameID 不一致 → 身份混淆 🔴
- **Destination/InResponseTo 未校验**：接受任意 SP 的 Response → 身份重放 🟠
- **依赖**：passport-saml <3.x 历史漏洞；java opensaml 须验 AudienceRestriction

## IP 来源伪造（访问控制）

> **前提**：core.md `trusted_proxy=none` 时，所有 X-* 头均可被客户端伪造；以下为各框架具体体现。

- `trust proxy` 未配置/过宽（Express `app.set('trust proxy', true)` 无反代）→ `X-Forwarded-For` 任意伪造 → IP 白名单绕过 🔴
- 认证/rate limit 基于 `req.headers['x-forwarded-for']`（可伪造）而非 `req.ip`（框架处理后）→ 🔴
- Java：`request.getRemoteAddr()` vs `getHeader("X-Forwarded-For")` 取值；Spring 未配置 ForwardedHeaderFilter 时 `X-Forwarded-For` 直读 → 🔴
- 检查：IP 白名单逻辑中取值来源；反代层是否过滤/覆写 XFF
- **X-User-Id / X-Tenant-Id 类内部头**：`trusted_proxy=none` 时外部可伪造 → 身份劫持 🔴；即使有反代，须确认反代**覆写**（非透传）这些头

## OAuth2/OIDC

PKCE 缺失(移动/SPA) → 🔴。Token 置换须验证 client_id 绑定。隐式授权 response_type=token → 🔴。state CSPRNG+一次性+绑定 session。redirect_uri 严格校验，禁开放重定向。code 一次性。

### Spring Authorization Server（检测到 spring-authorization-server 时）

RegisteredClientRepository client_secret 明文 → 🔴。未强制 PKCE（公开客户端）→ 🔴。动态客户端注册端点无认证 → 🔴。Token 自省/撤销端点无认证 → 🔴。

## 功能级授权

admin/manage/dashboard 路径 → 角色校验。仅前端隐藏 → 🔴。

## API 生命周期

路由含 deprecated/legacy/old/v1(且存在 v2+) → 废弃端点安全补丁可能未应用 🟡。

## WebSocket / Webhook

WebSocket → 见 checks-network.md。Webhook 签名/重放 → 见 checks-async.md。

## HTTP Method Override（ACL 绕过）

`X-HTTP-Method-Override: DELETE` / `X-HTTP-Method: PUT` / `_method=DELETE`（form POST）→ 部分框架/WAF 仅检查原始 HTTP 方法 → 🔴：
- Express `method-override` 中间件启用 + ACL 按 `req.method` 判断 → POST 请求伪装 DELETE 绕过权限
- Spring MVC `HiddenHttpMethodFilter`（表单 `_method`）→ 须确认只在需要表单 PUT/DELETE 时开启
- 防护：ACL 基于框架解析后的方法；若非必须禁用 method-override 中间件；REST API 无需 `_method`

## Token 生命周期（Rotation / 并行会话）

- **Token Rotation 缺失**：下发新 token 后旧 token 未立即失效 → 攻击者泄露旧 token 仍可使用 → 🟠。OAuth refresh token 轮换须同时吊销旧 token。
- **并行会话无限制**：同账户多地点登录无会话数量上限 → 凭证泄露后攻击者长期持有有效会话 → 🟡。
- **Confused Deputy**：服务 A 的 token 在服务 B 中被接受（未验证 `aud`）→ 权限混淆 → 🟠。JWT `aud` 须绑定目标服务。

## 服务间认证

内部 API 无认证+外部可达 → 🔴。X-User-Id header → 外部可伪造 → 🔴。  
unsupported-lang 服务 → 至少读 API 契约 → `[boundary:partial-audit]`。

## 竞态/Rate Limit/数据暴露

- 余额/库存 读-改-写 无 transaction/lock → 🟡；金融 → 🔴
- TOCTOU：getBalance→if→deduct 间有 await 无 transaction → 🟡/🔴
- 唯一性：findOne→create 非 upsert 无 unique 索引 → 🟡
- 登录/注册/重置/OTP 无 rate limit → 🟡
- 响应含 password_hash/token → 🟠/🔴
- 缓存 key 含用户可控部分无认证 → key 碰撞 🟡
- CDN cache key 不含 Auth → 用户 A 看到 B 数据 🔴

## 操作时序

先执行 DB 写/外部调用，后权限校验 → 🔴。
