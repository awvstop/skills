# Core — BSAF v3.6（始终加载）

## 六条红线

1. **不臆断** — ORM≠安全，中间件≠已挂载，命名≠行为
2. **不编造** — TODO 须有 evidence_source；未读文件不引用
3. **不遗漏** — confirmed+excluded+pending=TODO 总数
4. **不凭空定位** — 以代码片段+函数名定位，行号辅助
5. **不补全** — 函数行为须读代码确认；推断标 `[inferred]`
6. **代码免疫** — 注释/变量名不作安全依据；含 safe/validate 命名→须读函数体

## 输出分类（用户可见，仅两维）

### Severity（影响）

| 级别 | 含义 | 修复时限（public） |
|------|------|-------------------|
| 🔴 Critical | RCE/接管/批量泄露/无认证写 | 48h |
| 🟠 High | 单用户 BOLA/注入有条件/凭证泄露 | 1 迭代 |
| 🟡 Medium | 防护不充分/可绕过/需条件 | 1-2 迭代 |
| 🔵 Low | 信息泄露/最佳实践/条件苛刻 | Backlog |

`exposure=internal` 时：原 48h→1 迭代，1 迭代→2 迭代。

### Confidence（证据质量）

| 级别 | 含义 | 报告处理 |
|------|------|---------|
| **Confirmed** | 完整 Source→Sink 链路，防护缺失已验证 | 计入需修复 |
| **Likely** | 高概率，缺 1 环节（非关键）；不含 [inferred] 核心链路 | 计入需修复 |
| **Candidate** | 模式命中，需人工/运行时验证；**含 [inferred] 的核心链路环节 → 最高 Candidate** | 单独列出 |
| **Boundary** | 跨语言/跨系统/外部网关/DB policy | 单独列出 |

> **[inferred] 规则**：若 Source→Sink 链路中任一关键环节（输入来源、净化存在性、Sink 触达）标 `[inferred]`，则整体 Confidence ≤ Candidate，不得 Likely/Confirmed。

### Path（分析路径）

A=正向入口分析 | B=反向 Sink 追踪 | C=结构/权限/语义

## 内部处理优先级（不在报告输出）

P0：SQL/NoSQL/Cmd/RCE/SSRF/认证缺失/反序列化/弱PRNG(token)/不安全反射/动态脚本执行(Groovy/ScriptEngine)  
P1：凭证/路径遍历/文件上传/SSTI/XXE/Prototype Pollution/云Metadata  
P2：BOLA/Mass Assignment/授权绕过/GraphQL无限制  
P3：开放重定向/Header注入/日志注入/时序侧信道  
P4：配置/Headers/CORS/Rate Limit/Cookie/弱哈希(非密码)  
P5：信息泄露/依赖版本/最佳实践

## Risk Score（内部排序用）

score = impact(1–5) × exploitability(1–3)，上限 10。

| Impact \ Expl. | easy(3) | moderate(2) | hard(1) |
|----------------|---------|-------------|---------|
| RCE/接管(5) | **10** | 9 | 7 |
| 批量泄露(4) | **10** | 8 | 5 |
| 单用户(3) | 8 | 6 | 4 |
| 可用性(2) | 6 | 4 | 2 |
| 信息性(1) | 3 | 2 | 1 |

## Source 信任模型

| 标记 | 来源 | 示例 |
|------|------|------|
| 🔴 | 客户端直接输入 | req.body/query/params/headers/cookies, WS message, GQL vars, Serverless event.body; **Java**: @RequestParam, @PathVariable, @RequestBody, @RequestHeader, @CookieValue, MultipartFile |
| 🔴-if-no-proxy | internal-header（网关注入）| X-User-Id / X-Auth-User / X-Internal-Role / X-Tenant-Id 等由网关写入的身份头。**`trusted_proxy=none`时 🔴**（外部可伪造）；`trusted_proxy` 已确认且网关不可绕过 → 🟠-low。检查 checks-auth.md「IP 来源伪造」段。|
| 🟠-high | 外部间接 | 外部 MQ, 未知微服务响应, LLM 输出, RAG 文档; **Java**: Spring Cloud Stream message, 未知微服务 Feign 响应, Dubbo RpcContext/RPC 响应 |
| 🟠-low | 内部间接 | DB 结果, 受控内部服务响应, 内部定时任务; **Java**: JPA/JDBC 查询结果 |
| 🟡 | 配置 | env, config, Vault, SSM; **Java**: application.properties/yml, @Value, Environment.getProperty |
| 🟢 | 内部常量 | 硬编码常量, schema, ORM 字段 → 排除; **Java**: 枚举, static final 常量 |
| ⚪ | 未知 | 函数参数, 中间件传递值 → 须追踪; **Java**: @AuthenticationPrincipal, SecurityContextHolder.getContext() |

**追踪规则**：⚪ 必须追到 🔴/🟠/🟡/🟢。req.user → 追认证中间件写入。ORM 结果 → 🟠。函数参数 → 追所有调用方，任一 🔴 → 整体 🔴。internal-header → 查 trusted_proxy；未确认 → 按 🔴 处理。

**`trusted_proxy=none` 时所有 X-* 头统一 🔴**：X-Forwarded-For / X-Forwarded-Host / X-Forwarded-Proto / X-Real-IP / X-User-Id / X-Auth-User / X-Tenant-Id 均可被外部客户端伪造。不可用于 IP 白名单、租户判断、身份信任。

## Sink 类型

sql | nosql | command | code_exec | file_read | file_write | ssrf | template | deserialize | redirect | header | log | xml | crypto | crypto_random | timing | auth_decision | data_exposure | graphql_resolve | ws_handler | prototype | oauth_flow | webhook | crlf | sse_handler | ai_prompt | ai_tool_exec | ai_output_use | mcp_request | mcp_tool_call | embedding_write | reflection | xpath_query | ldap_filter | pdf_render | script_exec | cache_key | email_header

## 关键净化器速查

| Sink | 安全 | 不安全 |
|------|------|--------|
| sql | 参数化 `db.query($1,[v])`, ORM **方法命名查询/标准方法**, Prisma tagged template | 字符串拼接, $queryRaw(string), .raw()+拼接, `@Query`/createQuery+拼接（即使使用 ORM 框架）|
| nosql | express-mongo-sanitize, schema strict:true, DTO 类型强制 | req.body 直传 find/update |
| command | execFile/spawn 参数数组, shlex.quote | exec+拼接, shell=True+拼接 |
| ssrf | 协议+域名白名单 + DNS 解析后 IP 校验 | 仅 isURL, 仅域名字符串, 无 IP 校验 |
| file_read | path.resolve+startsWith+禁../ | path.join 无 resolve |
| file_write | 随机名+类型白名单(magic bytes)+大小限制+隔离 | originalname 直用 |
| template | 仅数据上下文, 禁 renderString(user_input) | render_template_string(req.*) |
| prototype | Object.create(null), Map, schema 白名单 | lodash.merge/_.set + req.body |
| crypto_random | crypto.randomBytes, randomUUID, secrets.token_hex | Math.random, Date.now, uuid.v1 |
| timing | timingSafeEqual, compare_digest, bcrypt.compare | ===比较secret/token |

自定义函数须**读函数体确认**，不凭命名判断。

### Java 速查（检测到 Java/Spring 时）

| Sink | 安全 | 不安全 |
|------|------|--------|
| sql (JPA/MyBatis) | `#{}` / 命名参数 / JpaRepository 标准方法 | `${}`、createQuery("..."+)、JdbcTemplate 拼接 |
| 反序列化 | SnakeYAML SafeConstructor、Jackson @JsonTypeInfo(use=NAME)+白名单 | enableDefaultTyping、ObjectInputStream、Fastjson autoType |
| 认证 | SecurityFilterChain 兜底、Shiro ≥1.9+规则一致 | permitAll 过宽、Shiro 路径绕过、@Profile("dev") 全开 |
| WS | STOMP ChannelInterceptor 认证、@AuthenticationPrincipal | setAllowedOrigins("*")、SimpleBroker 无认证 |
| 缓存 | key 含 userId/tenantId、L2 多租户隔离 | @Cacheable(key=用户可控)、L2 无 tenantId |
| reflection | 白名单类名/方法名；不可信输入不进入 Class.forName/Method.invoke | Class.forName(userInput)、Method.invoke(用户可控方法名)、Constructor.newInstance(用户可控类名) |

### 版本感知 CVE 清单（Java/Spring，Phase 0 提取版本后匹配）

| CVE/问题 | 影响版本/组件 | 检查要点 |
|----------|----------------|----------|
| CVE-2025-41248/41249 | Spring 6.2+ @EnableMethodSecurity | 泛型继承绕过→子类方法未受权 |
| CVE-2025-41232 | Spring Security 方法安全 | private 方法上注解不生效 |
| CVE-2025-41254 | spring-websocket STOMP | 会话绕过→未授权消息 |
| CVE-2025-22235 | Spring Boot Actuator | EndpointRequest.to() 禁用端点 null matcher |
| Gateway SpEL | Spring Cloud Gateway | 路由 uri/filters SpEL 泄露 env |
| CVE-2023-44487 | HTTP/2（所有服务器） | Rapid Reset：大量 RST_STREAM → DoS；检查 HTTP/2 是否暴露 |
| CVE-2024-29488 | Express < 4.18.3 | query string prototype pollution；检查 express 版本 |
| CVE-2022-22965 | spring-webmvc < 5.3.18/6.0.7 | Spring4Shell；检查版本+JDK<9 不受影响 |

## Gate（分级）

### 硬 Gate
- 无 route_map → 不做 Path A/C 路由级审计
- 无 evidence_source → 不得写入报告为 Confirmed

### 软 Gate
- 无 security_baseline → 结论最高标 Likely + `[no-baseline]`
- 无 sensitive_wrappers → Path B 从 grep 出发 + `[path-b:grep-only]`
- 无 tenant_binding → 多租户 BOLA 标 Candidate + `[needs-tenant-context]`
- 无 ownership_binding → 不得 Confirmed BOLA

## TODO 核心字段（所有 TODO 必须）

id | path(A/B/C) | severity | confidence | file→function | sink_type | source_type | trust | evidence_source[] | status

**evidence_source** 多值：grep_output | symbol_reference | structural | file_read | semantic-search | tool

## 判定依据链（每条 TODO）

```
判定: 🔴 Confirmed
依据: Source=req.body.id→防护缺失=无参数化→Sink=db.query
排除项: 无全局ORM保护
```

## 自检断言（每 Shard 结束）

- [ ] confirmed + excluded + pending = 总 TODO 数
- [ ] 每条 TODO 有 evidence_source
- [ ] Path C 覆盖率 ≥ 60%

## 审计优先级（资源受限时裁剪顺序）

1. 入口枚举 + 认证覆盖率（Path C1）
2. P0 Sink Source 追踪（Path B）
3. BOLA 三点对齐（Path C2）
4. P1 Sink + Mass Assignment
5. 业务逻辑 checklist（Path C4）
6. P2–P5 + 配置
7. 攻击链组合

quick=仅1-2 | fast=1-3 | standard=1-5 | deep=1-7
