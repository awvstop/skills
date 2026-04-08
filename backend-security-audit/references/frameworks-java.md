# Java / Spring Frameworks — BSAF v3.6

> 检测到 pom.xml / build.gradle / Spring Boot / Spring MVC / Spring WebFlux 时加载。自包含。

---

## Spring Boot 基础配置

### application.properties / application.yml

| 检查项 | 风险 |
|--------|------|
| `server.error.include-stacktrace=always` | 🟡 堆栈泄露 |
| `server.error.include-message=always` | 🟡 错误详情泄露 |
| `spring.jpa.show-sql=true`（生产） | 🟡 SQL 日志泄露 |
| `spring.datasource.password` 明文硬编码 | 🔴 凭证泄露 |
| `server.servlet.session.cookie.http-only=false` | 🟡 Cookie 不安全 |
| `server.servlet.session.cookie.secure=false`（生产） | 🟡 |
| `spring.profiles.active` 生产含 dev/debug | 🟡 |
| `management.endpoints.web.exposure.include=*` | 🔴 Actuator 全暴露 |
| `spring.jackson.deserialization.FAIL_ON_UNKNOWN_PROPERTIES=false` | 🟡 Mass Assignment 向量 |

### Spring Boot Actuator

| 端点 | 风险 |
|------|------|
| `/actuator/env` | 🔴 环境变量/凭证泄露 |
| `/actuator/heapdump` | 🔴 内存转储→凭证/session |
| `/actuator/mappings` | 🟡 路由结构泄露 |
| `/actuator/beans` | 🟡 内部架构泄露 |
| `/actuator/configprops` | 🔴 配置含凭证 |
| `/actuator/jolokia` | 🔴 RCE（JMX） |
| `/actuator/shutdown` | 🔴 DoS（若启用） |
| `/actuator/loggers` | 🟡 可动态修改日志级别 |

**检查**：Actuator 端点是否受 Spring Security 保护。`management.endpoints.web.exposure.include` 值。生产暴露非 health/info → 🔴。  
**CVE-2025-22235**：EndpointRequest.to(Endpoint) 在端点被禁用时可能产生 null matcher 放行请求 → 用 requestMatchers 显式路径替代。

---

## Spring Security

### 认证

- `SecurityFilterChain` / `WebSecurityConfigurerAdapter`（旧版）配置
- `.authorizeHttpRequests()` / `.authorizeRequests()` 规则顺序（**先匹配先生效**）
- `.permitAll()` 覆盖范围：过宽 → 🔴
- `.anyRequest().authenticated()` 是否存在（兜底规则）→ 缺失 🔴
- `@PreAuthorize` / `@Secured` / `@RolesAllowed` 覆盖率
- **规则顺序陷阱**：`.requestMatchers("/admin/**").permitAll()` 在 `.anyRequest().authenticated()` 前 → 管理端点无认证 🔴

### CSRF

- `.csrf().disable()` → 全局禁用须确认是否纯 API(无 cookie session)
- 纯 JWT 无状态 → 禁用 CSRF 可接受
- 有 session/cookie → 禁用 CSRF 🔴

### CORS

- `allowedOrigins("*")` + `allowCredentials(true)` → 🔴
- `@CrossOrigin` 注解逐处检查

### Session

- `SessionCreationPolicy.STATELESS` → 无状态 JWT
- `.maximumSessions(1)` → 并发控制
- `.sessionFixation().migrateSession()` → ✅

### 方法安全与近期 CVE（版本感知）

| CVE/问题 | 影响 | 检查 |
|----------|------|------|
| **CVE-2025-41248/41249** | @EnableMethodSecurity 泛型继承绕过 → 授权失效 | Spring 6.2+ 方法安全；子类/泛型方法是否被正确拦截 |
| **CVE-2025-41232** | private 方法上 @PreAuthorize/@Secured 不生效（AOP 不拦截） | 安全注解仅在 public 方法生效；private 方法内敏感逻辑 → 🔴 |
| **CVE-2025-41254** | STOMP over WebSocket 会话绕过 → 未授权消息 | 见 Spring WebSocket STOMP 段；Phase 0 提取 spring-websocket 版本 |
| **CVE-2025-22235** | EndpointRequest.to() 端点禁用时产生 null matcher → 放行 | 禁用 Actuator 端点时勿用 to(Endpoint); 用 requestMatchers 显式路径 |
| **Spring Cloud Gateway SpEL** | 路由配置中 SpEL 泄露环境变量 | 路由 uri/filters 中含 SpEL 且可被外部触发 → 🔴 |

Phase 0 提取框架版本后对照 core.md「版本感知 CVE 清单」匹配。

### Remember-Me 安全

- Remember-me key 硬编码 → 可伪造 token 🔴
- TokenBasedRememberMeServices 用 MD5 → 🟡；密码变更后 token 未失效 → 🟡
- Remember-me 用于敏感操作无二次认证 → 🔴

### 认证绕过模式

- **分号绕过**：`/admin;foo=bar` 匹配 `/admin` → 须 `StrictHttpFirewall`
- **尾斜杠**：`/admin` vs `/admin/` → Spring 6+ 默认不匹配
- **大小写**：`setUrlPathHelper` 大小写敏感性
- `.requestMatchers(HttpMethod.GET, "/api/**")` 仅限 GET → POST 同路径可能绕过

---

## Spring MVC

### Controller 入口

`@RestController` / `@Controller` + `@RequestMapping` / `@GetMapping` / `@PostMapping` / `@PutMapping` / `@DeleteMapping` / `@PatchMapping`。每个 handler method = 一个入口点。

### 参数绑定与 Mass Assignment

@RequestBody 直接绑定 JPA Entity → 🔴。@ModelAttribute 绑定含敏感字段 → 🟡。  
**安全**：DTO 接收→手动映射、`@JsonIgnoreProperties`、`@JsonProperty(access=READ_ONLY)`、`@Valid`+DTO 白名单。

### 输入校验

`@Valid`/`@Validated` + JSR-303 注解。缺少 `@Valid` → 🟡。`BindingResult` 未检查 → 🟡。

### 响应与数据暴露

Entity 直接返回（无 DTO）→ 可能暴露 password/内部字段 🟡。`@JsonIgnore`/`@JsonView` 控制。

### 开放重定向（Java Sink）

`return "redirect:" + request.getParameter("url")` → 🔴。`new RedirectView(userInput)` / `HttpServletResponse.sendRedirect(userInput)` / `new ModelAndView("redirect:" + userInput)` → 🔴。须白名单或固定目标。

### Java Records 作为 DTO

- Record 组件默认可反序列化；`@JsonProperty(access=READ_ONLY)` 在规范构造器上不生效 → 🟡
- 规范构造器可绕过 `@JsonIgnoreProperties` → 🟡
- 不可变 ≠ 安全；构造阶段仍需 `@Valid` 校验 → 🟡

---

## Spring Data JPA / Hibernate

| 方法 | 安全性 |
|------|--------|
| JpaRepository 标准方法 / 方法命名查询 / Specification / Criteria API | ✅ |
| `@Query("... WHERE id = :id")` JPQL/native 命名参数 | ✅ |
| JdbcTemplate `?` 占位符 / NamedParameterJdbcTemplate | ✅ |
| `@Query("... WHERE id = " + id)` 拼接 | ❌ 🔴 |
| `entityManager.createQuery/createNativeQuery("..." + input)` | ❌ 🔴 |
| `JdbcTemplate.query("..." + input, ...)` | ❌ 🔴 |

### BOLA 检查

`findById(id)` 无内置所有权绑定 → 须 Service 层校验 `order.getUserId().equals(user.getId())` 或 `findByIdAndUserId(id, userId)`。

---

## MyBatis

| 模式 | 安全性 |
|------|--------|
| `#{param}` | ✅ |
| `${param}` | ❌ 🔴 SQL 注入 |
| ORDER BY `${column}` | ❌ 🔴（须白名单） |
| LIKE `'%${keyword}%'` | ❌ 🔴（应用 `CONCAT('%',#{keyword},'%')`） |

**高频误用**：`${}` 用于动态表名/列名/ORDER BY。

---

## MyBatis-Plus

| 方法 | 安全性 |
|------|--------|
| `.eq("field", value)` / `.in("field", list)` | ✅ 参数化 |
| `.apply("id = {0}", value)` | ✅ 参数化 |
| `.apply("id = " + value)` | ❌ 🔴 SQL 注入 |
| `.last("limit " + value)` | ❌ 🔴 SQL 注入 |
| `.orderByAsc(userControlledColumn)` | ❌ 🔴 列名注入 |
| `.exists("SELECT ... WHERE " + value)` | ❌ 🔴 |
| `LambdaQueryWrapper` 链式 | ✅ 类型安全 |

---

## Groovy / ScriptEngine 动态执行

| Sink | 风险 |
|------|------|
| `new GroovyShell().evaluate(userInput)` | 🔴 RCE |
| `GroovyClassLoader.parseClass(userInput)` | 🔴 RCE |
| `ScriptEngine.eval(userInput)` (Groovy/JS/Nashorn) | 🔴 RCE |
| `Binding.setVariable("x", userInput); shell.run()` | 🔴（若 userInput 影响脚本逻辑） |
| `SecureASTCustomizer` 白名单 | 🟡 Candidate（可绕过，仍须关注） |

**常见场景**：规则引擎（Drools 非 DSL 场景）、低代码平台、动态配置执行。Phase 0 `grep -r "GroovyShell\|ScriptEngine\|GroovyClassLoader"` 加入 Sink 发现。

## H2 Console（测试 → 生产泄露）

- `spring.h2.console.enabled=true` + 生产部署 → `/h2-console` 未认证 → 任意 SQL → RCE（`CALL SHELLEXEC()`） 🔴
- 检查：application.properties 各 profile；Docker 镜像中是否带 dev profile 配置
- **grep**：`h2-console.enabled|CALL SHELLEXEC|H2ConsoleAutoConfiguration`

## Sa-Token 认证绕过

- `SaRouter.match("/**").check()` 配置顺序问题（同 Spring Security 规则顺序）→ 早期 permit 覆盖后续 check → 🔴
- Sa-Token < 1.34.0：部分版本路径匹配绕过（`/admin/` 尾斜杠）→ 历史 🔴
- `StpUtil.checkLogin()` 仅在 Service 层而非路由拦截器 → 缺漏端点 🔴
- `@SaCheckLogin` 注解仅对 Controller 方法；direct Service 调用不生效 → 🟡

## 注入类（Java 特有）

### SpEL 注入

`parseExpression(userInput)` → 🔴 RCE。`@PreAuthorize("hasRole('" + role + "')")` → 🔴。
**安全**：`@PreAuthorize` 用 `#param` 引用而非拼接。`SimpleEvaluationContext` → 相对安全。

**@Value + Config Server SpEL 注入链**：
- Nacos/Spring Cloud Config/Consul 配置值被 `@Value("#{...}")` 处理 → 配置中心可被写入（见 Nacos 无认证）→ SpEL 表达式 → RCE 🔴
- `@RefreshScope` + 动态刷新 → 攻击者写入 `#{T(java.lang.Runtime).getRuntime().exec("cmd")}` → refresh 触发 → RCE 🔴
- **区分**：`@Value("${key}")` = 普通属性替换（安全）；`@Value("#{expr}")` = SpEL 求值（危险）
- **检查**：grep `@Value\("#\{` 模式；配置来源是否受控；Nacos/Apollo 管理面认证

### EL / OGNL

JSP/JSF `${userInput}` → EL 注入 🔴。Struts2 → `[boundary:legacy-framework]` + 🔴。

### JNDI（Log4Shell 类）

`InitialContext().lookup(userInput)` → 🔴 RCE。Log4j2 < 2.17 + `logger.info(userInput)` → 🔴。  
检查 Log4j2 版本、JndiTemplate、JndiObjectFactoryBean。

### 模板注入（SSTI）

| 引擎 | 安全 | 危险 |
|------|------|------|
| Thymeleaf `th:text` | ✅ 转义 | `th:utext` 🟡 / `__${input}__` 预处理 🔴 RCE |
| Freemarker | — | Execute?new() 🔴 |
| Velocity | — | $rt.exec() 🔴 |

---

## 反序列化

| 场景 | 风险 |
|------|------|
| `ObjectInputStream.readObject()` / `XMLDecoder` | 🔴 RCE |
| Jackson `enableDefaultTyping()` / `@JsonTypeInfo(use=CLASS)` | 🔴 |
| Fastjson autoType 开启 | 🔴 |
| `SnakeYAML.load()` 无 SafeConstructor | 🔴 |
| `XStream.fromXML()` 无白名单 | 🔴 |
| Dubbo Hessian2/Kryo 反序列化不受信数据 | 🔴 RCE |
| Jackson `@JsonTypeInfo(use=NAME)` + 白名单 | ✅ |

### Gadget Chain 检测（Java ObjectInputStream 场景）

发现 `ObjectInputStream.readObject()` 接收外部数据时，须评估 classpath 中是否含已知 gadget 库：

| Gadget 库 | 版本 | 典型链 |
|-----------|------|--------|
| commons-collections | 3.x / 4.0–4.1 | CC1-CC7：InvokerTransformer → RCE |
| commons-beanutils | < 1.9.4 | CB1：PropertyUtils → RCE |
| spring-core | < 5.3.x | Spring1/Spring2：HierarchicalBeanFactoryPointcutAdvisor → RCE |
| rome | < 1.8.0 | ROME：ObjectBean → RCE |
| xalan / jdk7u21 | JDK < 7u21 | JDK7u21：原生类 → RCE（无需第三方）|
| groovy | < 2.5.x | Groovy：MethodClosure → RCE |

**检测策略**：
1. Phase 0 SCA 扫描上述组件版本
2. 发现 `ObjectInputStream` + 任一危险组件 → Confidence=Likely（即使未见完整利用路径）
3. 防护：SerialKiller/NotSoSerial 白名单过滤；或迁移至 JSON/Protobuf；或 `readObjectNoData` 覆盖
4. JEP 290（JDK 9+）序列化过滤器：检查是否配置 `jdk.serialFilter`

---

## SSRF（Java 特有）

RestTemplate / WebClient / `new URL().openConnection()` / OkHttpClient / Apache HttpClient / `Jsoup.connect()` + 用户可控 URL → 🔴。

---

## 文件操作

`new File(base + input)` 无规范化 → 🔴。`MultipartFile.getOriginalFilename()` 直用 → 🔴。  
**安全**：`Paths.get(base).resolve(input).normalize()` + `.startsWith(base)` → ✅。UUID 替代文件名。

---

## Spring WebFlux

`@RestController` + `Mono<>/Flux<>`。安全配置 `SecurityWebFilterChain`。R2DBC 参数化同 JdbcTemplate。

---

## AOP / Interceptor / Filter（认证审计核心）

### Filter Chain

- `OncePerRequestFilter` / `GenericFilterBean` / `Filter` 实现类 = 请求第一层处理
- **注册顺序**：`@Order` / `FilterRegistrationBean.setOrder()` → 低值先执行
- 认证 Filter 的 `shouldNotFilter()` → 绕过路径须逐一确认
- Filter 内异常未处理 → `chain.doFilter()` 仍执行 → 认证绕过 🔴

### HandlerInterceptor

- `preHandle` 返回 false → 终止；返回 true → 继续
- `excludePathPatterns()` → 排除路径须确认
- 非 Spring Security 项目中常为唯一认证层 → 须完整审计

### AOP 自定义权限注解

- @Aspect `@Around`/`@Before` pointcut 覆盖面
- 反射读取注解时继承/接口方法遗漏

### AOP 执行顺序安全影响

- `@Order` 值越小越先执行；日志 Aspect 若先于安全 Aspect 执行 → 未净化的输入先写入日志 → 日志注入/PII 泄露 🟡
- CGLIB 代理 vs JDK 动态代理：JDK 代理仅拦截接口方法；若安全注解标在实现类非接口方法上 → 代理不拦截 → 安全检查缺失 🔴
- 检查：安全相关 `@Aspect` 的 `@Order` 值；代理类型（`spring.aop.proxy-target-class`）

---

## @Transactional 审计

| 误用 | 后果 | 风险 |
|------|------|------|
| 同类内部 `this.method()` 调用 | 事务不生效 | 🔴 |
| `private` 方法上标注 | AOP 不拦截 | 🔴 |
| 默认 rollbackFor | 仅 RuntimeException 回滚 | 🟡 |
| `propagation=REQUIRES_NEW` 嵌套 | 部分提交 | 🟡 |
| 隔离级别 READ_COMMITTED（默认） | 金融需 SERIALIZABLE 或乐观锁 | 🟡 |
| `readOnly=true` 误用于写操作 | 部分 DB 静默忽略写入 | 🔴 |

---

## Spring Bean 并发安全

- **Singleton（默认）实例变量 = 所有请求共享** → 可变实例变量 🔴
- 检查：@Controller/@Service/@Component/@Repository 中非 final 非 ThreadLocal 的实例变量
- 安全：局部变量、方法参数、ThreadLocal、@Scope("prototype")、@RequestScope
- **@RequestScope / @SessionScope Bean 注入 Singleton**：`@Autowired UserSession session` 在 Singleton Bean 中 → Spring 用代理解决（正确）；若用构造器注入非代理 bean → 所有请求共享同一实例 🔴；须检查注入方式（`@Autowired` 字段注入 scoped bean 正确，构造器注入需 `proxyMode=ScopedProxyMode.TARGET_CLASS`）

---

## XXE 防御完整配置

| 解析器 | 关键禁用项 |
|--------|-----------|
| DocumentBuilderFactory | `disallow-doctype-decl=true` 或 external-general/parameter-entities=false + setExpandEntityReferences(false) |
| SAXParserFactory | 同上 feature |
| XMLInputFactory | IS_SUPPORTING_EXTERNAL_ENTITIES=false + SUPPORT_DTD=false |
| TransformerFactory | ACCESS_EXTERNAL_DTD="" + ACCESS_EXTERNAL_STYLESHEET="" |
| SAXReader (dom4j) | disallow-doctype-decl=true |
| SchemaFactory | ACCESS_EXTERNAL_DTD="" + ACCESS_EXTERNAL_SCHEMA="" |

仅设置部分属性 → 防护不完整 → 🟡。

---

## Lombok 审计注意

- `@Data`/`@ToString` → toString() 含所有字段 → 日志泄露密码 🟡
- `@Builder` → 绕过构造器校验；`@AllArgsConstructor` → 同上
- **检查**：`@ToString.Exclude` 是否标注敏感字段
- Lombok 生成代码不在源码可见 → 须理解注解语义

---

## Spring Data REST

- 依赖含 `spring-boot-starter-data-rest` → 所有 Repository 自动暴露 REST API
- `@RepositoryRestResource(exported=false)` 标注检查
- 自动 CRUD 无认证 → 🔴；Entity 含敏感字段直接序列化 → 🟡
- projection 配置是否限制暴露字段

---

## Spring Cloud 微服务

| 组件 | 检查 |
|------|------|
| **Gateway** | 路由配置、filter 顺序、SSRF(路由目标可控→🔴)、认证 filter 覆盖率；**路由 SpEL**：uri/filters 中含 SpEL 可泄露环境变量 → 🔴 |
| **Config** | 凭证暴露、/encrypt /decrypt 端点保护 |
| **Eureka/Nacos** | 服务注册可伪造→🔴、管理面板认证 |
| **Feign Client** | URL 拼接→SSRF；`@FeignClient(url=动态)` → 🔴 |
| **服务间认证** | 无认证→🔴；仅内网假设→🟡 |

### Spring Cloud Stream

- Consumer 方法 = 入口点，message payload = Source(🟠)
- 外部可投递 topic → 🔴；须校验消息来源
- 消息重放/重复消费 → 幂等检查

### Nacos 配置中心

- `@RefreshScope` Bean 属性运行时可变
- Nacos 管理面板无认证 → 🔴 配置注入
- 配置中明文凭证 → 🔴

### Sentinel / Resilience4j

- 关键接口限流规则审计
- Sentinel Dashboard 无认证 → 🔴
- 限流规则可 API 动态修改 → 需保护

### Spring Cloud Gateway 路由 SpEL

路由定义中 uri/filters 使用 SpEL 且输入可控或可泄露 env → 🔴。Phase 0 检查 gateway 路由配置。

---

## Apache Dubbo

- **Hessian2/Kryo 反序列化**：消费不受信数据 → RCE 🔴
- **服务注册伪造**：未鉴权注册中心 → 恶意服务注入 🔴
- **Dubbo Admin 无认证** → 🔴
- **RpcContext.getAttachments()** / 从 attachment 取参数 → Source 🟠-high；须校验来源

---

## Spring Security OAuth2 Resource Server

| 检查项 | 风险 |
|--------|------|
| JwtDecoder 未验证 issuer (iss) | 🟡 |
| JwtDecoder 未验证 audience (aud) | 🟡 |
| 对称密钥 (HS256) 硬编码 | 🔴 |
| JWKS URI 从 JWT header 动态取 | 🔴 JKU 攻击 |
| scope/authority 映射错误 | 🟡 权限绕过 |

---

## Spring Scheduler / @Async

@Scheduled 视同入口点。@Async 默认不传播 SecurityContext → 异步方法内无 user → 🔴。  
详见 checks-async.md Java/Spring 段。

---

## Java 21+ Virtual Threads 安全上下文

- **ThreadLocal 在 VT 复用时跨请求泄露**：SecurityContextHolder 使用 MODE_INHERITABLETHREADLOCAL 时，Virtual Thread 池复用导致上一请求的 SecurityContext 被下一请求读取 → 🔴
- **@Async 无 ContextPropagatingTaskDecorator**：VT 下异步任务不传播 SecurityContext → 安全上下文丢失 → 🔴
- **自定义 ThreadLocal\<TenantId\>**：VT 复用导致跨用户租户泄露 → 🔴
- **MDC 日志**：VT 切换导致请求 ID/用户关联错乱 → 🟡  
**检查**：Java 21+ 且启用 Virtual Threads（spring.threads.virtual.enabled=true 或 Executors.newVirtualThreadPerTaskExecutor）时，须使用 ScopedValue 或确保 SecurityContext 按请求隔离；@Async 须配置 TaskDecorator 传播上下文。详见 checks-async.md。

---

## Apache Shiro

### 路径匹配绕过（历史高危）

| 绕过方式 | 示例 | 影响版本 |
|---------|------|---------|
| 尾斜杠 | `/admin/` | <1.5.3 |
| 双斜杠 | `//admin` | <1.7.0 |
| 分号 | `/admin;bypass` | <1.7.1 |
| 路径遍历 | `/admin/..;/public` | <1.8.0 |
| 点斜杠 | `/admin/./` | <1.9.0 |
| Spring+Shiro 不一致 | 路径匹配差异 | 所有版本 |

检查 Shiro 版本、filterChainDefinitionMap、PathMatchingFilterChainResolver、anon/authc/perms/roles 覆盖率、自定义 Realm。

---

## Spring WebSocket STOMP

`@MessageMapping` / `@SubscribeMapping` = 入口点。

| 检查项 | 风险 |
|--------|------|
| `setAllowedOrigins("*")` | 🔴 |
| 无 `configureClientInboundChannel` 认证拦截器 | 🔴 |
| `@Payload` 无 `@Valid` | 🟡 |
| SimpleBroker 无认证 | 🔴 |
| StompBrokerRelay 凭证硬编码 | 🔴 |

**CVE-2025-41254**：STOMP over WebSocket 会话绕过 → 未授权消息。须验证 configureClientInboundChannel 认证拦截器与会话绑定；升级 spring-websocket 并对照 core.md CVE 清单。

---

## Content Negotiation → XXE

Accept: application/xml + XML MessageConverter 未禁 XXE → 🔴。  
检查 MappingJackson2XmlHttpMessageConverter / Jaxb2RootElementHttpMessageConverter、ContentNegotiationConfigurer、.xml 后缀。仅需 JSON → 移除 XML converter。

---

## Spring Boot DevTools

依赖含 `spring-boot-devtools` 且 scope 非 test/provided → 🔴。remote.secret → 远程热部署入口。

---

## Spring Boot Admin（检测到 spring-boot-admin 时）

| 检查项 | 风险 |
|--------|------|
| Admin Server 无 Spring Security 保护 | 🔴 可查看所有注册应用 Actuator 数据 |
| 暴露注册应用的 `/heapdump` / `/env` / `/configprops` | 🔴 凭证/内存泄露 |
| 注册端点（`/instances`）无认证 → 恶意应用可注册 | 🔴 |
| 可修改注册应用日志级别 / 触发 GC | 🟡 |
| Admin Client 的 `spring.boot.admin.client.url` 指向内部 Admin Server 且路径未限制 | 🟡 |

**grep**：`spring-boot-admin` / `@EnableAdminServer` / `AdminServerAutoConfiguration`

---

## Spring Profiles 安全

| 检查项 | 风险 |
|--------|------|
| `@Profile("dev")` Bean 禁用认证/CSRF | 🔴 若生产激活 |
| `spring.profiles.active` 可被覆盖 | 🟡 |
| `@ConditionalOnProperty("app.security.enabled")` | 🟡 可配置关闭 |

---

## Spring Cache (@Cacheable)

| 检查项 | 风险 |
|--------|------|
| cache key 不含 userId/tenantId | 🟡 跨用户命中 |
| @Cacheable 用于认证/授权结果 | 🔴 权限变更不生效 |
| Redis TTL 过长+敏感数据 | 🟡 |

---

## Spring GraphQL (spring-graphql)

`@QueryMapping` / `@MutationMapping` / `@SubscriptionMapping` = 入口点。DataFetcher/@SchemaMapping = resolver。  
认证用 `@PreAuthorize`。DataLoader → N+1 授权。Introspection/depth/cost 同 checks-network GraphQL 段。

---

## Hibernate 二级缓存

Entity 上 `@Cache` → 跨 Session 共享。多租户 key 不含 tenantId → 跨租户泄露 🔴。`use_second_level_cache=true` + 敏感 Entity → 审查隔离。

---

## 嵌入式服务器安全配置

| 配置 | 风险 |
|------|------|
| `server.tomcat.relaxed-path-chars` | 路径绕过向量 🟡 |
| Undertow `allow-encoded-slash=true` | 🟡 |
| Jetty `sendServerVersion=true` | 🔵 信息泄露 |

## 对象映射库与 DTO 绕过

| 用法 | 风险 |
|------|------|
| `BeanUtils.copyProperties(source, target)` 无排除 | 映射 isAdmin/role 🟡 |
| MapStruct @Mapper 默认全同名字段 | 🟡 |
| `ObjectMapper.convertValue(reqBody, Entity.class)` | 🔴 绕过 DTO 白名单 |

## 常见安全库识别

| 库 | 安全判定 |
|---|---------|
| Spring Security | 须验证配置完整性 |
| spring-boot-starter-validation | 须有 `@Valid` 触发 |
| Apache Shiro | 检查 filter 链 + 版本 |
| Sa-Token | 检查拦截器覆盖率 |
| `java.security.SecureRandom` | ✅ |
| `java.util.Random` 用于安全上下文 | 🔴 |
| OWASP ESAPI | ✅ |
| Hutool | 部分方法不安全（HttpUtil） |

---

## Java Spring 高危模式速查（Top 20）

| # | 模式 | 严重性 | 常见度 |
|---|------|--------|--------|
| 1 | MyBatis/MyBatis-Plus `${}` / `.apply()+拼接` | 🔴 | 极高 |
| 2 | Actuator 端点生产全暴露 | 🔴 | 高 |
| 3 | `@RequestBody` 直绑 JPA Entity | 🔴 | 高 |
| 4 | Spring Security 规则顺序错误 | 🔴 | 中 |
| 5 | Jackson `enableDefaultTyping()` | 🔴 | 中 |
| 6 | Shiro 路径绕过（低版本） | 🔴 | 高(国内) |
| 7 | Singleton Bean 可变实例变量 | 🔴 | 高 |
| 8 | Fastjson autoType | 🔴 | 中(国内) |
| 9 | JPA createQuery/createNativeQuery 拼接 | 🔴 | 中 |
| 10 | @Transactional 同类调用不生效 | 🔴 | 高 |
| 11 | Thymeleaf `__${input}__` 预处理 | 🔴 | 低 |
| 12 | SpEL `parseExpression(userInput)` | 🔴 | 低 |
| 13 | Spring Data REST 自动暴露 | 🔴 | 中 |
| 14 | 路径参数分号绕过 | 🟠 | 中 |
| 15 | @Async SecurityContext 不传播 | 🟠 | 高 |
| 16 | Virtual Thread ThreadLocal 泄露（SecurityContext/TenantId） | 🔴 | 高(Java21+) |
| 17 | @EnableMethodSecurity 泛型继承绕过（CVE-2025-41248） | 🔴 | 中 |
| 18 | Spring Cloud Gateway SpEL 环境变量泄露 | 🔴 | 中 |
| 19 | MapStruct/BeanUtils 自动映射绕过 DTO 白名单 | 🟠 | 高 |
| 20 | 不安全反射 Class.forName(userInput) | 🔴 | 低 |
