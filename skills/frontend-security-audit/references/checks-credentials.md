# 硬编码凭证 — v6

**高置信（grep阶段扫描）：**
```
sk-[a-zA-Z0-9]{32,}           OpenAI
AKIA[0-9A-Z]{16}              AWS
ghp_[a-zA-Z0-9]{36}           GitHub
AIza[0-9A-Za-z\-_]{35}        Google
xox[bpoas]-[0-9a-zA-Z-]{10,}  Slack
sk_live_[a-zA-Z0-9]{24}       Stripe Secret
pk_live_[a-zA-Z0-9]{24}       Stripe Publishable
AC[a-f0-9]{32}                Twilio
DefaultEndpointsProtocol       Azure
glpat-[A-Za-z0-9\-_]{20}      GitLab PAT
npm_[A-Za-z0-9]{36}           npm token
```

**变量名：** `(api_?key|secret_?key|password|passwd|pwd|token|auth|credential)\s*[:=]\s*['"][^'"]{8,}['"]`

**§jwt JWT（Phase 1内联检测，不在grep阶段）：**
- 仅标记字符串字面量赋值：`const/let/var xxx = "eyJ..."` 或 `{ key: "eyJ..." }`
- 排除：函数返回值 · API响应变量 · Authorization header动态拼接 · 模板字面量中的变量 · 类型定义
- 命中时：验证是否为硬编码token(非运行时获取) → 是=P1凭证 · 否=排除

**排除：**
- 值：YOUR_*/SAMPLE_*/EXAMPLE_*/<TOKEN>/xxx/changeme/placeholder/全相同字符/00000000
- 来源：process.env.*/import.meta.env.*/Deno.env.get/函数调用 → 排除
- 变量名：左侧含type/name/label/header/key_name/description → 排除
- 路径：test/fixtures/mock/__tests__/stories/examples → 🔵+"测试代码，确认不含真实凭证"

**配置：** .env/config.js/settings.js硬编码 · .npmrc/.yarnrc _authToken · .sentryclirc token
