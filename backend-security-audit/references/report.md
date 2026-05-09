# Report — BSAF v3.6

## Executive Summary

**本报告**对当前项目做高覆盖后端安全审计，优先发现高风险问题，产出证据链。

## 一页概览

项目 | 日期 | 总体风险(🔴/🟡/🟢) | 高危数 | 攻击链数 | 缺认证 API % | 敏感操作缺授权 % | Top 3 最紧迫 | 审计置信度(High/Medium/Low) | 覆盖率

## 优先修复项（Top 5）

| 优先级 | 发现 | 复杂度(低<4h/中1-3d/高>3d) | 建议时限 | 依赖 |

## Attack Surface Summary

| 类别 | 数量 | 高风险项 |
|------|------|---------|
| Public API Routes | | |
| Authenticated/Admin Routes | | |
| File Upload/External HTTP | | |
| GraphQL/WebSocket/gRPC/SSE | | |
| Queue Handlers/Internal Calls | | |
| OAuth2 Flows | | |

## 报告头

- 日期 | 模式 | BSAF v3.6
- 技术栈 | 架构类型
- 路由总数 R | 缺认证 M
- Confirmed A | Likely B | Candidate C | Boundary D
- 攻击链 CH
- 使用的 reference 文件清单

## 凭证脱敏（必须）

>12 位：首尾各 3 位 + 遮蔽。≤12 位：全遮蔽 `[Sensitive Key Detected]`。

## 🔴🟠 高危 — 完整格式

位置 | 脱敏代码片段 | 成因 | 链路 | POC | Severity | Confidence | OWASP-API | OWASP-Web | fingerprint | **修复方向**（1-2 句）| context_lines

## 🟡🔵 — 压缩表格

编号 | Severity | Confidence | 位置→函数 | 类型 | Sink | Source | OWASP | 修复方向

## 攻击链 — 完整格式

关联 V-xxx | 组合效果 | 升级 | 利用路径 | Confidence

## 降级扫描发现（[downgrade]）

来源目录 | 摘要 | Confidence 上限 Likely

## Candidate / Boundary

编号 | 位置 | Sink | 原因 | 建议操作

## 修复方向映射

| 漏洞类型 | 修复方向 |
|----------|----------|
| SQLi | 参数化查询；禁字符串拼接 |
| BOLA/IDOR | 查询条件绑定 req.user.id；复合路径逐级校验 |
| SSRF | 协议+域名白名单；DNS 解析后 IP 校验；禁跟随重定向 |
| Mass Assignment | DTO whitelist；ValidationPipe(whitelist:true) |
| SSTI / Prototype→RCE | 禁用户输入进模板字符串；深合并用 Object.create(null) |
| 命令注入 | execFile/spawn 参数数组；禁 shell:true 拼接 |
| 路径遍历 | path.resolve + startsWith(base)；禁 ../ |
| 文件上传 | magic bytes 校验 + 类型白名单 + 随机文件名 + 隔离目录 |
| 弱随机 | crypto.randomBytes / SecureRandom |
| 认证缺失 | 添加全局认证中间件；补 anyRequest().authenticated() |
| 时序侧信道 | timingSafeEqual / compare_digest |
| ReDoS | 改用 re2；避免嵌套量词 |
| XXE | 禁外部实体；disallow-doctype-decl=true |
| 反序列化 | safe_load；禁 enableDefaultTyping；SerialKiller 白名单 |
| OAuth | state(CSPRNG)+PKCE(S256)+redirect_uri 严格校验 |
| Webhook | HMAC 签名验证 + timestamp+nonce 重放防护 |
| MyBatis ${} | 替换为 #{}；动态列名/ORDER BY 用白名单映射 |
| SpEL 注入 | SimpleEvaluationContext；禁 parseExpression(userInput) |
| Actuator 暴露 | exposure.include 仅 health/info；Security 保护其余端点 |
| Fastjson autoType | 升级 Fastjson2；禁 autoType |
| Shiro 路径绕过 | 升级 ≥1.9.0；启用 StrictHttpFirewall |
| Jackson defaultTyping | @JsonTypeInfo(use=NAME) + 白名单 |
| @RequestBody 直绑 Entity | 改用 DTO + 手动映射 |
| @Transactional 误用 | rollbackFor=Exception.class；避免同类内调用；禁 private 方法标注 |
| VT 上下文泄露 | ContextPropagatingTaskDecorator；ScopedValue 替代 ThreadLocal |
| CVE-2025-41248 泛型绕过 | 升级 Spring Security ≥6.4.11 或子类重声明注解 |
| Dubbo 反序列化 | 改用 triple+protobuf；或配置序列化白名单 |
| 不安全反射 | 白名单 Map 映射替代 Class.forName(userInput) |
| 开放重定向 | 白名单域名；禁 // 开头 URL |
| Spring AI 注入 | 系统提示与用户输入参数化分离；@Tool 参数 schema 校验 |
| H2 Console | spring.h2.console.enabled=false（生产） |
| 二阶注入 | 存入时净化；取出后进危险 Sink 前再校验 |
| Host Header 注入 | BASE_URL 固定于配置；禁用 Host header 构造 URL |
| Cache Deception | 敏感 API 强制 Cache-Control: private, no-store |
| Cache Poisoning | 影响响应的头加入 Vary；敏感响应加 Cache-Control: private, no-store |
| Session Fixation | 登录成功后 regenerate session ID |
| JWT 算法混淆 | 硬编码 algorithms 列表；非对称场景禁接受 HS256 |
| SAML XSW | validateSignatureOnResponse 覆盖整个 Response |
| HTTP Method Override | REST API 禁用 method-override 中间件 |
| Groovy/ScriptEngine | 禁用户输入直接 eval；改用规则 DSL |
| HTTP/2 Rapid Reset | 升级服务端；配置 maxConcurrentStreams 限制 |
| 反序列化 Gadget Chain | SerialKiller 白名单过滤；迁移 JSON/Protobuf；配置 jdk.serialFilter |
| Token Rotation | 下发新 token 同时吊销旧 token；验证 JWT aud 绑定目标服务 |
| 服务间认证 | mTLS 或 JWT issuer+audience 绑定；禁止仅内网假设 |
| K8s ServiceAccount | RBAC 最小权限；Secret 用 valueFrom.secretKeyRef |
| Prompt Injection | 系统提示与用户输入参数分离；禁字符串拼接进 prompt |
| RAG 投毒 | 外部文档嵌入前净化；metadata 不控制工具调用 |
| 整数溢出 | 业务字段类型强验证；金融计算用 BigDecimal |

## 已知局限（必须包含）

1. Grep 无法捕获动态方法/运行时路由/反射
2. 上下文窗口限制跨文件追踪深度
3. 仅静态分析，无运行时验证
4. 第三方库内部不审查
5. BOLA 需结合业务上下文人工确认
6. 仅覆盖 Node.js/Python/Java，其他语言标 [boundary:unsupported-lang]
7. 攻击链基于已发现漏洞推理

**本次特定局限**：覆盖文件数/总数、跳过的大文件、Candidate 数量、未覆盖框架语言（partial-audit）边界数。

## Coverage Metrics

files_scanned | routes_analyzed | sinks_verified | noise_ratio | path_c_coverage | shard_coverage

## OWASP 映射

BOLA→API1 | 认证→API2 | Mass Assignment→API3 | 资源消耗→API4 | 功能授权→API5 | 业务流程→API6 | SSRF→API7 | 配置→API8 | 注入→A03 | 凭证→A07 | 弱加密→A02 | 反序列化→A08

## fingerprint 格式

`[file:function]::sink_type::vuln_type::source_type`  
链：`chain::[V-xxx+V-yyy]::组合类型::效果`

## JSON Schema（output_format=json）

```json
{
  "schema_version": "bsaf-v3.6",
  "metadata": {},
  "summary": { "risk_level":"", "high_count":0, "chain_count":0, "confidence":"" },
  "findings": [{ "id":"", "severity":"", "confidence":"", "path":"", "file":"", "function":"", "sink":"", "source":"", "fix_direction":"", "fingerprint":"", "evidence_source":"", "counter_evidence":"", "owasp":"" }],
  "chains": [],
  "pending": [],
  "coverage": {}
}
```
