# 跨 Skill 严重性与信心词汇映射

> 本文件为套件级共享规范。各 Skill 内部使用不同词汇体系，本表用于跨 Skill 交接时的翻译。

---

## 严重性对照

| 统一级别 | backend (BSAF) | frontend (CEVF) | verify-findings | jira-report (CVSS 参考) |
|----------|---------------|-----------------|-----------------|------------------------|
| CRITICAL | 🔴 （RCE/接管/全量泄露/未认证写） | 🔴 （可控Source→无防护，直接可利用） | CRITICAL | CVSS ≥ 9.0 |
| HIGH | 🟠 （单用户BOLA/有条件注入/凭证泄露） | 🔴 （需条件但影响大） | HIGH | CVSS 7.0–8.9 |
| MEDIUM | 🟡 （防护不充分/可绕过/需交互） | 🟡 （防护不充分/可绕过/需特定条件） | MEDIUM | CVSS 4.0–6.9 |
| LOW | 🔵 （信息泄露/最佳实践/条件苛刻） | 🔵 （信息泄露/配置缺失） | LOW | CVSS 0.1–3.9 |
| INFO | — | — | INFO | CVSS 0.0 |

> **注意**：backend 🔴 对应 CRITICAL，🟠 对应 HIGH。frontend 仅用三级（🔴/🟡/🔵），🔴 可能对应 CRITICAL 或 HIGH，须结合利用条件判断。

---

## 信心/结论词汇对照

| 语义 | backend (BSAF) | frontend (CEVF) | verify-findings |
|------|---------------|-----------------|-----------------|
| 已确认可利用 | Confirmed | ⚠️confirmed (traced+exploitable) | ✅确认 |
| 高概率，缺一环 | Likely | ⚠️confirmed (traced+conditional) | ✅确认 或 ⚠️降级 |
| 模式命中，需验证 | Candidate | ⚪待确认 | ⏸️存疑 |
| 跨边界/外部依赖 | Boundary | ⚪待确认 + "需后端确认" | ⏸️存疑（边界项） |
| 经证据排除 | excluded | excluded | ❌误报 |
| 已知风险接受 | — | — | 💡已知风险接受 |
| 降级后仍需关注 | Likely（降级） | ⚠️confirmed（降级） | ⚠️降级 |

---

## 交接规则

### backend → verify-security-findings
- Confirmed → 以 ✅确认 为目标，补 Step 1 入口证据后可直接确认
- Likely → 重点补证缺失环节，通常可确认或降级
- Candidate → ⏸️存疑 起点，需完整 Step 0~6
- Boundary → Step 1/2 快速确认后标「边界项，建议专用工具补充」

### frontend → verify-security-findings
- ⚠️confirmed (traced+exploitable) → Confirmed 等价，可直接确认
- ⚠️confirmed (traced+conditional) → Likely 等价，补证后确认或降级
- ⚪待确认 → Candidate 等价，需完整验证

### verify-findings → jira-security-report
- CRITICAL/HIGH ✅确认 → 立即生成报告，附 PoC
- MEDIUM ✅确认 → 生成报告
- ⚠️降级 → 视调整后级别决定是否生成报告
- ❌误报 → 不生成报告
- ⏸️存疑 → 暂不提单，补充信息后重验
