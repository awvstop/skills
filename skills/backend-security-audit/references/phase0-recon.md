# Phase 0: RECON — BSAF v3.6

> 轻量侦察，不读源码正文。产出 recon-profile。

## 产出分级

### Tier 1（必须，缺失则审计不启动）
- backend_root + stack_profile + architecture_type
- route_map（至少入口列表）
- sink_hits（至少 Grep 粗召回已执行）
- shard_plan

### Tier 2（应当，缺失则降级不阻断）
- security_baseline
- security_controls
- sensitive_wrappers
- trusted_proxy
- dependency_risk_summary

### Tier 3（按需）
- resource_model_summary（BOLA≥5 / 多租户 / 复合路径 / deep 模式）
- tenant_boundary_summary（检测到 tenant/org）
- ai_inventory（检测到 AI 库）

## §0.1 后端根目录 + 技术栈（限读 ≤8 文件）

读取根文件树 + package.json / requirements.txt / pyproject.toml / pom.xml / build.gradle / Dockerfile / docker-compose.yml / serverless.yml / **application.yml** / **application.properties**（限读 ≤**10** 文件；需提取版本号、VT/H2/Admin 配置）。

- **backend_root**：用户 scope / monorepo 后端包 / server|api|backend 目录。纯前端 → 终止并提示。
- **architecture_type**：serverless 特征 → serverless；多服务/gateway → microservice；否则 monolith。
- **stack_profile**：runtime, framework, orm, auth, api_style, architecture_type, backend_root.
- **Java/Spring**：检测 pom.xml（`spring-boot-starter-web/webflux/security`）/ build.gradle（`org.springframework.boot`）。产出 stack_profile 含 runtime=java, framework=spring-boot, orm=jpa/mybatis, auth=spring-security/shiro/sa-token。**提取版本号**用于 core.md CVE 清单匹配。

  **依赖触发表**（检测到以下依赖时自动触发对应审计段）：

  | 依赖标识 | 触发 |
  |---------|------|
  | `spring-ai-*` | checks-ai.md Spring AI 段 |
  | `spring-authorization-server` | checks-auth.md Spring Authorization Server 段 |
  | `dubbo-spring-boot-starter` / `dubbo` | frameworks-java.md Dubbo 段 |
  | `sa-token-spring-boot-starter` | frameworks-java.md Sa-Token 段 |
  | `spring.threads.virtual.enabled=true`（application.yml）| frameworks-java.md Virtual Threads 段 |
  | `spring.h2.console.enabled=true` | frameworks-java.md H2 Console 段（直接 TODO: 🔴）|
  | `spring-boot-admin-*` | frameworks-java.md Spring Boot Admin 段 |
  | Spring Boot / Security 版本 | core.md CVE 清单匹配 |
- **其他语言**：未识别为 Node/Python/Java 时，stack_profile 标 runtime=other；入口按项目结构（如 Go: main/router、C#: Controllers、Ruby: config/routes、PHP: public/index）；grep 取 Core 段通用 pattern。结论标 `[boundary:partial-audit]`。

### 网关 / 反向代理识别（trusted_proxy）

检测 nginx.conf / gateway.yml / kong.yml / envoy.yaml / AWS ALB/CloudFront / Traefik 配置：

```yaml
trusted_proxy:
  type: nginx|kong|envoy|aws-alb|cloudfront|none
  x_forwarded_for_trusted: true|false   # 决定 IP 来源是否可信
  x_forwarded_host_trusted: true|false  # 决定 Host Header 是否可信
  auth_offload: true|false              # 网关是否已做认证（如 AWS Cognito）
  evidence: [文件路径]
```

- `trusted_proxy.type=none` → Express trust proxy / Spring ForwardedHeaderFilter 任何信任均为 🔴
- `auth_offload=true` → 后端内部 API 的认证可能依赖网关层；须确认网关不可绕过
- 后续 Source 模型使用：`x_forwarded_for_trusted=false` 时 X-Forwarded-For 信任级别升为 🔴

### SCA 依赖风险扫描（dependency_risk_summary）

解析依赖文件，识别已知高危组件（无需工具，版本号对比即可）：

| 组件 | 危险版本 | 风险 |
|------|---------|------|
| log4j-core | < 2.17.1 | 🔴 RCE (Log4Shell) |
| fastjson | < 2.0.26（1.x 全危） | 🔴 反序列化 RCE |
| jackson-databind | < 2.13.4.2 含 polymorphic | 🔴 反序列化 |
| snakeyaml | < 2.0 | 🔴 反序列化 RCE |
| commons-collections | 3.x / 4.0–4.1 | 🔴 反序列化 gadget（4.2+ 安全）|
| commons-text | < 1.10.0 | 🔴 StringSubstitutor RCE |
| netty | < 4.1.86 | 🟠 HTTP Smuggling/DoS |
| spring-webmvc | < 5.3.18 / 6.0.7 | 🟠 Spring4Shell(CVE-2022-22965) |
| xstream | < 1.4.20 | 🔴 反序列化 RCE |
| shiro-core | < 1.9.0 | 🔴 路径绕过 |
| netty | < 4.1.86 | 🟠 HTTP Smuggling/DoS；< 4.1.68 🔴 HTTP/2 DoS |
| spring-webmvc | < 5.3.18 或 6.0.x < 6.0.7 | 🟠 Spring4Shell(CVE-2022-22965)（JDK<9 不受影响）|
| Node.js express | < 4.18.3 | 🟠 query string prototype pollution (CVE-2024-29488) |

> **版本范围说明**：表中"危险版本"含义为"该范围内的版本存在已知漏洞"；`X.Y.Z+` 表示该版本起修复，但须独立验证后续版本未引入新漏洞。传递依赖不在此表覆盖范围（建议外部工具辅助）。

产出：`dependency_risk_summary`（受影响组件 + 版本 + CVE + 风险等级）。发现 🔴 依赖 → 直接进入 TODO 列表，Confidence=Likely，须 Phase2 确认利用路径。

## §0.2 Sink 发现（四步）

### Step 1: Grep 粗召回（必做）
按 grep-patterns.md（取 runtime+framework 子集）执行。标 `[source:grep_output]`。

### Step 2: 入口点枚举（必做）
按框架找所有 API 入口（不依赖 grep）：

| 框架 | 搜索 |
|------|------|
| Express/Fastify/Koa | app.get/post/…, router.* |
| NestJS | @Get/@Post/@Controller |
| Django | urls.py urlpatterns |
| FastAPI | @app.get, @router.*, APIRouter |
| Next.js | app/api/**/route.ts, pages/api/**, "use server" 函数 |
| Nuxt/Nitro | server/api/**, defineEventHandler |
| Elysia/Hono | new Elysia(), new Hono() |
| Spring MVC | @GetMapping/@PostMapping/@PutMapping/@DeleteMapping/@PatchMapping/@RequestMapping, @RestController 所在类 |
| Spring WebFlux | @RestController + Mono/Flux 返回, RouterFunction 定义 |
| Spring RouterFunction（函数式） | RouterFunction<ServerResponse>, RouterFunctions.route(), RequestPredicates |
| Spring Cloud Gateway | application.yml routes 配置 |
| Spring WebSocket STOMP | @MessageMapping, @SubscribeMapping, registerStompEndpoints |
| Spring GraphQL | @QueryMapping, @MutationMapping, @SchemaMapping |
| Shiro 路由 | ShiroFilterFactoryBean.filterChainDefinitionMap |
| Spring Filter/Interceptor | OncePerRequestFilter 子类, HandlerInterceptor 实现, FilterRegistrationBean |
| Spring Scheduler | @Scheduled 方法 |
| Spring Cloud Stream | @StreamListener, Consumer<Message<T>> 函数式 Bean |
| Spring Data REST | JpaRepository 子接口（若含 data-rest 依赖则自动暴露） |

产出：**route_map**（method + path + handler 位置）

### Step 3: 符号追踪补充（必做）
- P0/P1 Sink → Find All References 查调用方
- 入口 handler → Go to Definition 追到 service 层
- 产出 sink_hits_symbol，与 Step 1 合并去重

### Step 4: 外部工具（可选）
semgrep / npm audit / pip audit 可用则执行。不可用 → 跳过并记录 `[external-tool:unavailable]`。超时 60s → 终止。执行失败 → 禁止重试，立即降级回 grep。

### 合并
同文件同行号(±5行) → 保留信息最丰富的。产出最终 **sink_hits**。

## §0.3 security_baseline（Tier 2）

```yaml
security_baseline:
  global_auth: { mechanism, skip_annotations, file }
  global_validation: { mechanism, file }
  orm_safety: { default, raw_query_count }
  rate_limit: { global, per_route }
  multi_tenant: { context_source, enforcement }
  error_handling: { global_handler, stack_trace_exposure }
```

**采集指引**：
- `global_auth`：grep `SecurityFilterChain|app\.use.*auth|OncePerRequestFilter|@PreAuthorize` → 找注册点 → 读函数体确认覆盖范围；`skip_annotations` = `@Public/@SkipAuth/@PreAuthorize("permitAll")`
- `global_validation`：grep `@Valid|@Validated|ValidationPipe|class-validator` → 是否为全局 Pipe
- `orm_safety`：grep `.raw(|createNativeQuery|${}` → 计数为 raw_query_count
- `rate_limit`：grep `rateLimit|throttle|RateLimiter|@Throttle` → 判断全局/路由级
- `error_handling`：grep `@ControllerAdvice|app\.use.*error|errorHandler|@ExceptionHandler` → 是否含 stack trace

## §0.4 降级扫描（轻量 grep，不跳过）

migrations/ seeds/ → SQL 拼接、硬编码凭证
.env.example / .env.* / config/*.json / settings.py → 凭证 pattern
**bootstrap.yml / bootstrap.yaml** → Spring Cloud 早期加载配置，优先级高于 application.yml
**configmap*.yaml / values.yaml** → K8s ConfigMap / Helm，明文 secret / 敏感配置
**docker-compose*.yml** → environment 明文凭证、端口暴露
.github/workflows/ .gitlab-ci.yml → secrets 引用
__tests__/ *.test.* → 硬编码 Key/JWT
templates/ → SSTI
结果并入 sink_hits，标 `[downgrade]`。

## §0.5 Shard 计划

优先级 = 攻击面风险 × Sink 密度。high_risk_zones 强制前两 Shard。[shared] Shard 建议首位。

**Shard 分配算法**：
1. 按 P0/P1 Sink 密度排序文件 → 密度最高的文件组成前两 Shard（high_risk）
2. 按路由父 handler 分组：同一 Controller/Router 文件的路由归同一 Shard
3. 单文件 > 2MB → 独立 Shard（头尾+采样）；不与其他文件合并
4. `[shared]` 公共工具函数/中间件 → 独立首位 Shard，所有其他 Shard 可引用
5. 剩余文件按 Sink 密度递减分组，每 Shard ≤ 2000 行预算

**recon-profile 不完整处理**：若 Tier 1 字段不完整（sink_hits=0 但有 entrypoints，或 route_map 空但有明显框架路由注解）→ 补充侦察再进 Phase 1，标 `[recon:partial]`；不强制终止，以已有 entrypoints 启动 Shard 1。

**快速退出**：Sink=0 且无 entrypoints → "无 API 入口，建议确认 backend_root"。
**>2MB 文件**：头尾+采样。**自动生成代码**：GENERATED BY → `[skip:autogen]`。

## §0.6 输出

recon-profile 全部字段 + 续接提示：「Phase 0 完成，N Sink / R 路由(M 缺认证) / K Shard。输入 `继续` 进入 Shard 1。」
