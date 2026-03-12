# Python Frameworks — BSAF v3.6

## Django

- .raw()/.extra()/RawSQL/cursor.execute 拼接 → 🔴。F()/Q() 安全。
- @login_required/permission_required 每处验证。AllowAny 逐处确认。
- DEBUG=True 生产 → 🔴。ALLOWED_HOSTS=['*'] → 🟡。SECRET_KEY 硬编码 → 🔴。
- serializer 无 fields/__all__ → Mass Assignment。
- CSRF：csrf_exempt 逐处验证。
- **Django Admin**：`/admin/` 生产暴露 + INSTALLED_APPS 含 `django.contrib.admin` → 无 IP 限制/2FA → 🟠。弱 superuser 密码 → 🔴（后台 RCE 链：Template 自定义 → SSTI）
- **QuerySet 注解注入**：`annotate(order=RawSQL(f"... {user_input} ...", []))` → 🔴
- **ATOMIC_REQUESTS=True**：视图异常回滚全部 DB 操作，但并发读-改-写仍需 select_for_update()

## Jinja2

- `Environment(autoescape=False)` → 模板渲染用户数据 → XSS/HTML Injection 🟡；若有 `{{userInput}}` 且模板字符串来自用户 → SSTI 🔴
- `Markup(userInput)` 强制信任用户数据 → 🟡
- `render_template_string(userInput)` → SSTI 🔴（同 Flask 段）
- Flask 默认对 `.html` 模板 autoescape=True；对 `.txt` → False

## Flask

- app.debug/FLASK_DEBUG 生产 → 🔴(Werkzeug debugger RCE)
- render_template_string(user_input) → SSTI 🔴
- send_file(user_input) → 路径遍历
- @app.route 无认证装饰器 → 逐条检查
- WTForms CSRF → 覆盖率检查

## FastAPI

- Pydantic 天然白名单
- Depends(get_current_user) 覆盖率；无全局依赖时每路由显式声明
- response_model 防过度暴露；Optional[dict]/Any → 可绕过验证
- /docs + /redoc 生产禁用 → 🟡
- WebSocket 认证同 checks-network

## Tornado / Sanic

- **Tornado**：get_argument 自动解码；write(user_input) → SSR XSS；check_xsrf_cookie 覆盖率
- **Sanic**：middleware 执行顺序；blueprint 中间件覆盖率

## ORM

- **SQLAlchemy**：text()+拼接 不安全；text($1).bindparams() 安全。session.execute(text(f"...")) → 🔴
- **Tortoise**：.raw() 不安全；.filter() 安全；.execute_query() 拼接不安全
- **Peewee**：.raw() 拼接不安全；Model.select().where() 安全
- **Django ORM**：标准查询安全；.raw()/.extra()/RawSQL 拼接不安全

## 反序列化

- pickle.load → 🔴。yaml.load(无 SafeLoader) → 🔴。yaml.safe_load → ✅
- torch.load(weights_only=False) → 🔴

## 任务队列

- **Celery**：@task=handler；参数=Source(🟠)；accept_content 限制；result_backend 暴露
  - **pickle serializer（🔴 RCE）**：`CELERY_TASK_SERIALIZER = 'pickle'` 或 `accept_content = ['pickle']` + 外部可投递 broker（公网 Redis/RabbitMQ）→ 任意 pickle 反序列化 → RCE 🔴。安全：`accept_content = ['json']`；broker 绑定内网；认证凭证非默认
  - **result_backend**：`CELERY_RESULT_BACKEND = 'redis://...'` 结果可读 → 任务返回值泄露（含 token/PII）；Redis 无认证 → 🔴
  - **task routing**：`task_routes` 可将任务路由到不同 queue；若 queue 名来自 payload → 🟠

## 安全库识别

- defusedxml → XXE 安全
- itsdangerous → token 签名（检查 secret 来源）
- PyJWT → jwt.decode 检查 algorithms/verify 参数
- passlib/bcrypt → 密码哈希安全
- bleach → HTML 净化
