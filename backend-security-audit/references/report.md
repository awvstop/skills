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

SQLi→参数化 | BOLA→绑定 req.user.id | SSRF→白名单+DNS 校验+禁重定向 | Mass Assignment→DTO whitelist | SSTI/Proto→RCE→禁用户输入进模板/深合并 | Cmd→execFile 参数数组 | 路径遍历→resolve+startsWith | 文件上传→magic bytes+随机名 | 弱PRNG→crypto.randomBytes | 认证缺失→添加中间件 | 时序→timingSafeEqual | ReDoS→re2 | XXE→禁外部实体 | 反序列化→safe_load | OAuth→state+PKCE+redirect 验证 | Webhook→签名+重放防护 | MyBatis ${}→替换为#{},动态列名白名单 | SpEL→SimpleEvaluationContext | Actuator→限制exposure仅health/info+Security保护 | Fastjson→升级Fastjson2+禁autoType | Shiro绕过→升级≥1.9.0+StrictHttpFirewall | Jackson defaultTyping→@JsonTypeInfo(NAME)+白名单 | @RequestBody Entity→DTO映射 | @Transactional→rollbackFor=Exception.class+避免同类调用+禁private | VT上下文泄露→ContextPropagatingTaskDecorator+ScopedValue替代ThreadLocal | 泛型注解绕过(CVE-2025-41248)→升级Spring Security≥6.4.11或子类重声明注解 | Dubbo反序列化→triple+protobuf或序列化白名单 | 不安全反射→白名单Map映射替代Class.forName | 开放重定向→白名单域名+禁//开头 | Spring AI注入→系统提示隔离+@Tool参数schema校验 | H2 Console→生产禁用spring.h2.console.enabled=false | 二阶注入→存入时净化+取出后进危险Sink前再校验 | Host Header→BASE_URL固定于配置禁用Host构造URL | Cache Deception→敏感API强制Cache-Control:private,no-store | Cache Poisoning→敏感头加入Vary或CDN cache key+敏感响应Cache-Control:private,no-store | Session Fixation→登录后regenerate session ID | JWT算法混淆→硬编码algorithms列表禁HS256(非对称场景) | SAML XSW→validateSignatureOnResponse覆盖整个Response | Method Override→禁用method-override中间件(REST API) | Groovy/ScriptEngine→禁用户输入直接eval,用规则DSL替代 | HTTP/2 Rapid Reset→升级服务端+配置maxConcurrentStreams限制+速率限制RST_STREAM | 反序列化Gadget Chain→SerialKiller白名单过滤+迁移JSON/Protobuf+配置jdk.serialFilter | Token Rotation→下发新token同时吊销旧token+验证JWT aud绑定目标服务 | 服务间认证→mTLS或JWT issuer+audience绑定+禁止仅内网假设 | K8s ServiceAccount→RBAC最小权限禁cluster-admin+Secret用valueFrom.secretKeyRef | Prompt Injection→系统提示与用户输入参数分离禁字符串拼接 | RAG投毒→外部文档嵌入前净化+元数据不控制工具调用 | 整数溢出→业务字段类型强验证+BigDecimal金融计算

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
