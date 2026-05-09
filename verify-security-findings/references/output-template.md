# 输出模板与验证汇总格式

> SKILL.md 仅保留输出规则摘要；本文件为完整模板，验证时按需加载。

---

## 单条 Finding 输出模板（chat 中直接输出）

每条验证完毕的 finding 按以下结构输出，重点突出三要素：验证结论、依据、实际危害。

```
### Finding: [编号] [标题]
原始级别: CRITICAL / HIGH / MEDIUM / LOW
线索来源: [BSAF 输入时填 evidence_source/counter_evidence/classification；非 BSAF 时填：用户粘贴片段 / grep 输出 / 手工审计报告 / report 目录报告摘要 / .audit 中间产物 / security-audit-report 摘要；**不可为空**]
BSAF fingerprint: [若有则填，便于与审计报告对账]
实现证据: [至少两处关键片段为宜：如 Sink + 入口或断点之一；文件:行号 或配置路径；⏸️ 时写「未读：<原因>」。**不得填写** `report/`、`.audit/`、`.bsaf/` 或 `security-audit-report*.md` **内容**]

**【验证结论】** ✅确认 / ❌误报 / ⚠️降级 / 💡已知风险接受 / ⏸️存疑挂起
**【依据】** [一句话核心理由；须与「已读源码」一致；关键位置 文件:行号 或 函数名/路由]
**【实际危害】** [若确认/降级：外部攻击者能做什么、影响范围；若仅内部攻击面请明确标注；若误报：无；若存疑：待补充]

---（可选细项）---
Step 1 入口可达性: [可达/不可达] — [证据]
Step 2 信任边界: [跨界/未跨界] — [依据]
Step 3 可控性: [完全/部分/间接/不可控] — [依据]
Step 4 数据流: [通过/阻断] — [关键节点与断点]
Step 5 Sink危害: [具体攻击效果]
Step 6 利用前提: [现实/不现实]
调整后级别: CRITICAL / HIGH / MEDIUM / LOW / INFO / FALSE POSITIVE / KNOWN RISK
复现概要: [CRITICAL/HIGH 确认时必填（1～3 步攻击路径：攻击者起点→请求→结果）；其余级别确认后填写；写不出则改为 ⏸️存疑]
实测状态: [未实测 / 已实测 / 实测受阻] — [已实测：附请求/响应关键摘要；实测受阻：说明原因并主动建议用户复测；纯静态分析得出的 ✅ 默认填「未实测」]
反例假设: [CRITICAL/HIGH ✅ 必填：「若本条为误报最可能的原因是 X」+ 已查证依据（grep 命中 / 文件:行号 / 已读片段）；查不出反例才出 ✅，否则 ⏸️存疑]
修复方向: [一句话建议]
待补充信息: [无 / 具体缺失项]
同类批量: [无 / 同根因覆盖 #XX,#XX]
```

**与 BSAF 分类对应**：Confirmed→✅确认；Likely→重点补证后可为确认或 ⚠️降级；Candidate→验证后多为存疑或降级；Boundary→Step 1/2 快速确认后标「边界项」。

**判定倾向（防误判）**：证据模棱两可时优先标**存疑**并列出待验证项；缺少「外部可触发」证据时不得判 `✅确认`。

---

## 组合利用链审视

**触发条件**：存在 ≥2 条非 FALSE POSITIVE 的 finding，且至少有一条级别为 MEDIUM 或以下；或存在不同攻击阶段的 finding 组合。全部为误报时跳过。

**经典组合示例**：
- 信息泄露 + SSRF → 内网穿透
- 路径遍历 + 文件包含 → RCE
- IDOR + 越权 → 批量数据泄露
- 配置泄露 + 认证绕过 → 系统接管
- 低危 XSS + 高权限操作 → 管理员会话劫持
- SSRF + 云元数据 → 凭证窃取
- SQL 注入(有限) + 信息泄露 → 完整数据提取
- Prompt 注入 + Agent Tool(exec/文件) → 间接 RCE
- IDOR(读) + Mass Assignment(写) → 篡改他人数据

若组合成立，在 chat 中单独输出一条组合链 finding，标注关联编号，独立定级。

**默认**：在验证汇总中增加「潜在组合（待确认）」小节；用户说 **「深度组合分析」** 再补充详细组合可行性。

---

## 验证结果汇总模板（chat 中直接输出）

```
## 验证汇总

| 统计项 | 数量 |
|--------|------|
| 原始 finding 总数 | X |
| ✅ 确认（需修复） | X |
| ⚠️ 降级 | X |
| 💡 已知风险接受 | X |
| ❌ 误报 | X |
| ⏸️ 存疑挂起 | X |
| 🔗 组合链 | X |

### 调整后级别分布（可选）
CRITICAL: X | HIGH: X | MEDIUM: X | LOW: X | INFO: X | FALSE POSITIVE: X | KNOWN RISK: X

### 修复优先级排序（仅含确认 + 降级 + 组合链）
1. [CRITICAL/HIGH] Finding #XX — [标题] — [一句话理由]
2. [MEDIUM] Finding #XX — ...

### 潜在组合（待确认）
- Finding #A + #B：[一句理由]

### 存疑项待补充信息汇总
- Finding #XX: 需要 [具体信息]（补全后可继续验证该条）
```

如需生成报告文件或 Jira 工单，由用户另行调用「Jira 安全报告」等 report 类 Skill。

---

## 严重性定级标准

| 级别 | 定义 | 典型场景 |
|------|------|----------|
| CRITICAL | 未认证远程利用 + 系统级影响 | 未认证 RCE；全量数据泄露；认证体系完全绕过 |
| HIGH | 认证后高危利用或大范围数据影响 | 认证后 RCE；批量敏感数据泄露；任意文件读写；管理员接管 |
| MEDIUM | 需交互或条件限制 + 中等影响 | 存储型 XSS；有条件 SSRF；单用户数据泄露；水平越权 |
| LOW | 有限影响或利用门槛极高 | 反射型 XSS(需点击)；非敏感信息泄露；仅影响自身 |
| INFO | 最佳实践/理论风险 | 版本号泄露；冗余 Header；无实际利用路径 |
| FALSE POSITIVE | 误报 | 经验证漏洞前提不成立 |
| KNOWN RISK | 已知风险接受 | 非误报但为设计权衡，有补偿控制；须标注补偿措施 |

---

## BSAF / CEVF 交接映射

| 语义 | BSAF（后端） | CEVF（前端） | 本 Skill |
|------|------------|------------|---------|
| 已确认可利用 | Confirmed | ⚠️confirmed (traced+exploitable) | ✅确认 |
| 高概率缺一环 | Likely | ⚠️confirmed (traced+conditional) | ✅确认 或 ⚠️降级 |
| 模式命中需验证 | Candidate | ⚪待确认 | ⏸️存疑 |
| 跨边界/外部依赖 | Boundary | ⚪待确认+"需后端确认" | ⏸️存疑（边界项） |

严重性映射：BSAF 🔴=CRITICAL、🟠=HIGH、🟡=MEDIUM、🔵=LOW；CEVF 🔴 对应 CRITICAL 或 HIGH（按利用条件）、🟡=MEDIUM、🔵=LOW。

BSAF 输入时优先利用 **evidence_source**、**counter_evidence**、**classification** 作为定位线索；仍须在仓库内打开对应文件复核。Likely/Candidate 项重点补证缺失环节；Boundary 项可快速做 Step 1 入口与信任边界确认后标注「边界项」。
