# Infra / Config / Supply Chain / Logging — BSAF v3.6

> 凭证、HTTP 头、CORS、环境、云、容器、供应链、错误处理、日志。自包含。

## 凭证

硬编码凭证/密钥 → 🔴。.env 提交/可访问 → 🔴。降级扫描覆盖 .env.example/config/*.json/settings.py。

## HTTP 安全头 / CORS

HSTS/X-Content-Type-Options/X-Frame-Options。CORS *+敏感 API → 🔴。
请求体大小未限制(JSON>10MB) → 🟡 DoS。

**CORS 精细化**：
- `Access-Control-Allow-Origin: null` → file:// / sandboxed iframe 跨域请求成功 🔴
- Origin 动态反射（`if (origin) res.setHeader('ACAO', origin)`）+ credentials=true → 任意跨域读取 🔴
- Origin 正则前缀/后缀匹配（`origin.endsWith('.trusted.com')`）→ `evil.trusted.com` 绕过 🟠
- `allowCredentials: true` + `allowedOrigins: *` → Spring CORS 会拒绝（框架保护），但手动实现可能不检查

## 环境条件分支

NODE_ENV/DEBUG/FLASK_DEBUG 条件中调试路由/开放 CORS/禁用认证 → 🟡。NODE_ENV 未设置默认非 production。

## Swagger/OpenAPI 生产暴露

FastAPI /docs /redoc、NestJS SwaggerModule、/swagger.json 生产暴露 → 🟡。

## 云 / Serverless / 容器

- IAM 过宽、S3 公开、metadata 未禁(IMDSv1) + SSRF → 🔴
- /var/run/secrets/kubernetes.io/serviceaccount/token 可被 SSRF → 🟡
- Docker Socket /var/run/docker.sock → 容器逃逸 🔴
- K8s API 可达 + SSRF → 🔴

## Kubernetes / Container 精细化

- **ServiceAccount 权限过宽**：Pod 挂载 `automountServiceAccountToken: true`（默认）+ RBAC `cluster-admin` / `*` verbs → SSRF → K8s API 全控 🔴
- **Secret 明文 env**：`env.value: <secret>` 明文（非 valueFrom.secretKeyRef）→ 容器 `/proc/self/environ` 可读 🟡；`kubectl describe pod` 可见
- **privileged: true**：容器逃逸 → 宿主机 root 🔴
- **hostPath 挂载**：`/` / `/etc` / `/var/run/docker.sock` → 逃逸 🔴
- **网络策略缺失**：Pod 间无 NetworkPolicy → 横向移动不受限 🟡

## 供应链

- **依赖混淆**：@scope 包未配私有 registry → 🟡。pip --trusted-host 跳 TLS → 🟡
- **Lock 完整性**：package.json 无 lock → 🟡；lock registry 不一致 → 🟡
- **Dockerfile**：FROM latest → 🟡。curl|bash → 🟡。ARG/ENV 敏感信息未清理 → 🟡。.dockerignore 未排除 .env/.git → 🟡

## CI / GitHub Actions

- **脚本注入**：`run: echo "${{ github.event.pull_request.title }}"` → PR 标题含 `$(cmd)` → 🔴 RCE on runner。所有 `github.event.*` 用户可控字段不得直接插入 `run:` 步骤；须通过 env 变量传递
- **Action 版本钉**：`uses: actions/checkout@v4`（非 SHA）→ tag 可被劫持 → 供应链 🟡；高安全要求须 `uses: actions/checkout@<full-sha>`
- **过宽权限**：`permissions: write-all` / `secrets: inherit` → 🟡；最小权限原则
- **secrets 泄露**：`echo $SECRET` / `env: SECRET: ${{ secrets.KEY }}` 传入第三方 action → 🟡；secrets 不应出现在 run: 输出

## 全局错误处理

- Express 无 4 参数错误中间件 → 🟡
- 错误响应含 stack trace/SQL 详情/内部路径 → 🟡
- Promise rejection 未 catch → DoS 🟡

## 日志安全

- logger.info(req.body) / 日志含 JWT/session ID → 🟡
- 日志注入：用户输入含 \n → 假日志行 🟡
- catch 泄露敏感信息 → 🟡
