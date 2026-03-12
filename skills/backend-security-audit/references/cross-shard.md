# Cross-Shard — BSAF v3.6

> 所有分片完成后加载。攻击链组合规则唯一定义于此。

## 流程

1. 汇总所有 Shard todo-list
2. 识别跨 Shard 数据流
3. [shared] 函数影响范围 → 复制到受影响 Shard
4. 服务间调用边界标记
5. 组合升级（见下）
6. 更新 todo-list

**门槛**：仅由 Confirmed/Likely 组成的发现参与 CHAIN 组合。Candidate/Boundary 不参与升级。

## Level 1：必做组合（6 条高频）

| V-a | V-b | 组合效果 | →🔴 |
|-----|-----|---------|------|
| SSRF | 无云 metadata 防护 | 读取云凭证 | ✓ |
| 认证缺失 | 敏感数据暴露(同端点) | 未认证访问敏感数据 | ✓ |
| BOLA(读) | Mass Assignment(写) | 读+篡改他人数据 | ✓ |
| Prototype Pollution | 模板引擎(EJS/Pug) | RCE | ✓ |
| 弱 PRNG(token) | Session/认证 | 会话劫持 | ✓ |
| 文件上传(不完整) | 路径遍历(同模块) | Webshell | ✓ |

## Level 2：数据流关联（推荐）

V-a 的 Sink 是 V-b 的 Source，或共享数据存储 → 检查组合利用。

## 扩展组合（参考）

| V-a | V-b | 组合效果 |
|-----|-----|---------|
| SSRF | 内部服务无认证 | 横向移动 |
| Prototype Pollution | 授权检查(isAdmin) | 越权 |
| Prompt Injection | Agent Tool(exec/file) | 间接 RCE |
| Prompt Injection | DB 查询(AI 生成) | 恶意 SQL |
| 间接 PI(RAG) | PII in context | 跨用户泄露 |
| Webhook 无签名 | 内部 API | 伪造调用 |
| SSRF | Redis/内网可达 | 未授权写→RCE |
| Mass Assignment | isAdmin 字段 | 全系统接管 |
| 日志注入 | 日志解析系统 | 代码执行 |
| Actuator /env 暴露 | SSRF | 读取凭证→接管数据库/云 |
| Shiro 路径绕过 | 敏感端点(admin/payment) | 未认证访问管理/支付 |
| Spring Data REST 自动暴露 | Entity 含敏感字段 | 未认证 CRUD + 数据泄露 |
| Fastjson autoType | 外部 JSON 输入端点 | 反序列化 RCE |
| Host Header 注入 | 密码重置邮件 | 账号接管（邮件含攻击者域名）|
| SVG/HTML 文件上传 | admin 面板/用户浏览 | Stored XSS → admin 上下文执行 |
| 二阶注入(stored) | 后台 job/admin 查询 | 延迟触发 SQLi/RCE |
| SSRF(gopher://) | Redis 无认证 | FLUSHALL/任意写→RCE |
| JWT 算法混淆(伪造 token) | BOLA | 任意账号接管 |
| Method Override(POST→DELETE) | 功能级授权仅限 GET/POST | 越权删除/修改 |
| GitHub Actions 注入 | CI secrets 泄露 | 代码库/云环境接管 |
| Gateway SpEL 环境泄露 | Actuator /env 暴露 | 凭证窃取→云/DB 接管 |
| Virtual Threads 上下文泄露 | 支付/PII 处理逻辑 | 跨用户数据暴露/越权 |
| @EnableMethodSecurity 泛型绕过 | 敏感业务端点 | 未授权操作（CVE-2025-41248）|
| Dubbo 反序列化（Hessian2/Kryo） | 内部服务无认证 | 横向移动+RCE |
| Spring AI @Tool 无参数校验 | DB/Exec Sink | Agent 工具滥用→注入/RCE |
| Nacos 管理面无认证 | @RefreshScope Bean | 运行时配置注入→禁安全/RCE |
| H2 Console 生产暴露 | SSRF 可达或直接访问 | CALL SHELLEXEC → RCE |
| Sa-Token 路径绕过 | 敏感端点（admin/payment） | 未认证访问管理/支付 |

## 缓存攻击链（Level 1 补充）

| V-a | V-b | 组合效果 | →🔴 |
|-----|-----|---------|------|
| Host Header 注入 | 缓存层 key 含 Host（Cache Poisoning） | 投毒其他用户缓存页面 | ✓ |
| Cache Deception（敏感端点无 Cache-Control: no-store） | BOLA / 数据暴露 | 攻击者读取他人缓存的私有响应 | ✓ |

## 分散式漏洞（跨 ≥3 Shard）

| 模式 | 效果 |
|------|------|
| 分散配置弱化（CORS+SkipAuth+敏感路由） | 未认证跨域访问 |
| 分散信任传递（X-User-Id 伪造链） | 身份伪造 |
| 分散净化遗漏（入口 A 校验、入口 B 不校验同一 Service） | 绕过注入 |
| 分散 ThreadLocal 依赖（SecurityContext+TenantContext+MDC）+ Virtual Threads | 多维度上下文泄露（用户/租户/日志全错乱）|

## Shard 状态快照格式

```yaml
shard_stub:
  shard_id: N
  todos: ["T-001|sql|db.query(${id})|🔴|🔴 Confirmed"]
  open_sources: []
  boundary_calls: []
```

同类漏洞 >10 → 前 3 详细 + pattern_match 合并。

## 对话模式降级

早期 Shard 不在上下文 → 请用户粘贴 shard_stub。无法获取 → `[cross-shard:partial]`，总体评级标「不可靠」并上调一级。
