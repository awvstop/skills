# Node.js Frameworks — BSAF v3.6

## Express / Fastify / Koa

**Express**：
- app.use/router 顺序=执行顺序；错误中间件在认证前=跳过认证
- express.static('.') → 根目录暴露 🔴
- cors() 无配置=* → 🔴(含 cookie)
- trust proxy 无真实代理 → IP 伪造
- express.urlencoded(extended:true) → 深层对象 → Prototype Pollution 向量
- res.redirect(req.query.next) → 开放重定向
- HPP：?role=user&role=admin → 数组绕过 🟡

**Fastify**：JSON Schema 验证、onRequest/preHandler 认证、reply.sendFile(params.file) → 路径遍历。removeAdditional:true → 防 Mass Assignment。

**Koa**：洋葱模型、ctx.state.user 追踪。

## NestJS

- @UseGuards(AuthGuard) + @Public/@SkipAuth 每处验证
- **ValidationPipe(whitelist:true)** → 防 Mass Assignment；默认 whitelist:false → 透传
- DTO 无装饰器字段 + whitelist:false → Mass Assignment
- GraphQL resolver → 同 controller 认证
- 微服务 @MessagePattern → handler 内认证

## Hapi / tRPC / Elysia / Hono / Nitro

- **Hapi**：config.auth 默认策略、Joi 验证、payload maxBytes
- **tRPC**：publicProcedure vs protectedProcedure、input schema(Zod)、ctx.user 来源、batching 限制
- **Elysia(Bun)**：类似 Express；Bun 运行时部分 Node 漏洞需按运行时判定
- **Hono**：多运行时(Workers/Bun/Deno/Node) → 安全 API 差异
- **Nitro/H3**：defineEventHandler，event.node.req = req

## ORM

- **Prisma**：$queryRaw`` 安全、$queryRaw(string) 不安全
- **Sequelize**：.query() 拼接不安全、sequelize.literal 不安全
- **Mongoose**：$where 字符串 → 代码执行 🔴；操作符注入 → 🔴；schema strict:false → Mass Assignment
- **Drizzle**：sql`` 安全、sql.raw() 不安全
- **TypeORM**：createQueryBuilder().where("..."+v) 不安全

## 动态模块加载

- `require(userInput)` / `import(userInput)` → 任意模块加载/路径遍历 → RCE 🔴
- `require('child_process')[req.query.method](req.query.cmd)` → 组合 🔴
- JSON.parse reviver 含 eval/Function：`JSON.parse(data, (k,v) => eval(v))` → 🔴
- **安全**：模块名白名单；禁用动态导入用户可控路径

## Next.js / Nuxt 服务端安全

- **Server Actions** (`"use server"`)：默认无 CSRF 保护（Next.js 14+ 有内置 origin check，但需验证配置）；action 内直接用 `cookies()` / `headers()` 须校验来源
- **Server Components**：误将 secret 变量直传 Client Component → 泄露到客户端 bundle 🔴
- **Route Handlers** (`app/api/**/route.ts`)：每个 export function = 入口点；检查 auth 包裹
- **getServerSideProps / getStaticProps**：`params.id` 未校验直接查询 → BOLA；`query` 用于数据库 → 注入
- **Nuxt/Nitro**：`defineEventHandler` 无 `auth` composable → 未认证路由；`event.node.req.url` 含 `../` → 路径遍历

## 任务队列

- **Bull/BullMQ**：process callback=handler；job.data=Source
- **Agenda**：define callback=handler

Source 信任按投递方：外部/Webhook→🔴，内部定时→🟠-low。

## 事件驱动

- **Kafka**(kafkajs)：consumer.run eachMessage=handler；外部可投递 topic → 🔴
- **RabbitMQ**(amqplib)：consume callback=handler；公网可投递 → 🔴
- **Redis Pub/Sub**：subscribe callback=handler
- **EventEmitter**：event/payload 来自网络须校验
