---
name: jira-dedupe
description: >
  对 report/ 下已有安全报告批量与 Jira 已有单（~/Zoom.mhtml）去重，识别 confirmed duplicate / possible duplicate / no match。
  Triggers: 报告去重, 检查重复, 和 Jira 已有单对比, 检查是否已报 Jira, dedupe reports, jira dedupe, 查重, 去重, check duplicates, 报告查重。
  两阶段流程：第一阶段候选筛选，第二阶段全文比对；判断由 LLM 完成，脚本仅提取材料。
alwaysApply: false
---

# Jira 安全报告去重 — 独立 Skill

**入口**：用户说「报告去重」「检查重复」「和 Jira 已有单对比」「检查是否已报 Jira」「查重」「dedupe reports」等，即对本地 report/ 目录下的安全报告与 Jira 已有单做重复判断。

---

## CONTRACT

**角色：** 安全工程师，负责在提 Jira 单之前识别本地报告与已有 Jira 工单的重复关系，避免重复提单。

**输入（固定）：**
- **Jira 已有单数据源**：`~/Zoom.mhtml`（用户手动导出的 Jira 搜索结果页面）
- **本地报告目录**：当前项目 `report/` 目录，或用户明确指定的路径/文件
- 若 `~/Zoom.mhtml` 不存在，提示用户先导出 Jira 搜索结果为 mhtml 并保存到 `~/Zoom.mhtml`

**核心工具：**
- 脚本路径：本 Skill 目录下 `scripts/zoom_jira_dedupe.py`
- 脚本职责**仅是提取并格式化材料**，不做重复判断；重复判断由 LLM 在对话中完成

---

## 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| mhtml_path | ✅ | Jira 导出文件路径，默认 `~/Zoom.mhtml` |
| report_dir | ✅ | 本地报告目录路径 |
| report_path | ❌ | 第二阶段指定单个报告 |
| jira_key | ❌ | 第二阶段指定 Jira 工单键 |
| strict | ❌ | 严格模式；缺输入时直接失败 |
| format | ❌ | `markdown`（默认）/ `json` |

---

## 两阶段去重流程

### Step 1 — 候选筛选

1. 运行：
   ```bash
   python <skill_dir>/scripts/zoom_jira_dedupe.py summary \
     --mhtml ~/Zoom.mhtml \
     --report-dir <report目录绝对路径> \
     --format markdown
   ```
2. 脚本输出「本地报告标题/漏洞类型」与「Jira 已有单标题/漏洞类型」摘要
3. LLM 基于摘要**仅筛选 candidate pairs**（偏召回：标题、模块、对象、攻击面、漏洞类型/CWE 任一明显接近即入选）
4. **禁止**在第一阶段给出 confirmed duplicate 结论

### Step 2 — 全文比对

1. 对第一阶段每个候选项运行：
   ```bash
   python <skill_dir>/scripts/zoom_jira_dedupe.py bundle \
     --mhtml ~/Zoom.mhtml \
     --report-dir <report目录绝对路径> \
     --report-path <candidate-report> \
     --jira-key <candidate-jira-key> \
     --format markdown \
     --strict
   ```
2. 脚本展开候选报告正文与候选 Jira Description 到 stdout
3. LLM 基于全文材料判断每对候选：
   - `confirmed duplicate` — 根因相同、触发路径相同、修复点覆盖
   - `possible duplicate` — 同类漏洞但触发路径或影响对象有差异，需人工复核
   - `no match` — 无关

### 判断规则

- 以 Jira Description 与报告正文的**语义一致性**为主判据
- 漏洞类型/CWE 和标题仅作辅助；同类 CWE 不能单独证明重复
- 必须结合**触发路径、影响对象、攻击方式、修复点**综合判断
- 若根因相同且合理修复会自然覆盖当前 finding，判 confirmed duplicate

---

## 输出规则

- 结论**仅在对话中输出**，格式清晰（表格或列表均可）
- **禁止**将去重结论、提取材料、Jira 标题/Description 缓存写入当前项目或 `report/` 目录
- 若用户显式要求落盘，只允许写到**仓库外路径**（通过 `--out` 参数指定）
- 输出内容包括：
  - confirmed duplicate：列出报告路径 + 对应 Jira key + 简要证据
  - possible duplicate：列出报告路径 + 对应 Jira key + 差异点
  - no match：可省略或简要列出

---

## 对话输出约束

- **禁止**过程性铺垫话术（如「正在分析…」「开始去重…」）
- 第一阶段结束后，简要列出候选对数量，直接进入第二阶段
- 第二阶段结束后，输出最终结论表格/列表
- 若存在 confirmed duplicate，**必须明确提醒**用户在提单前去除这些重复项
- 若仅存在 possible duplicate，标为"疑似重复"并提示用户人工复核

---

## 快捷命令

- 用户说「看看 Zoom.mhtml 里有哪些单」→ 仅运行 `extract` 子命令：
  ```bash
  python <skill_dir>/scripts/zoom_jira_dedupe.py extract \
    --mhtml ~/Zoom.mhtml \
    --format markdown
  ```
  输出到 stdout，不修改项目代码。

- 用户指定单个报告去重（如 `@report/xxx.md 查重`）→ 第一阶段可跳过，直接运行 bundle 对该报告全量比对。

---

## 禁止项

- **禁止**自动触发去重——必须由用户显式请求
- **禁止**脚本内做重复判断——脚本只提取材料
- **禁止**将任何去重产物写入 `report/`、项目根目录或 `.audit/` 等目录
- **禁止**修改本地报告文件内容（如自动标注 duplicate）
- **禁止**在无 `~/Zoom.mhtml` 时编造 Jira 数据或凭记忆判断重复

## 脚本参数补充

- `summary --strict`：当 `--report-dir` 下没有任何 `.md` 报告时直接失败
- `bundle --strict`：当 `--report-dir` 无报告，或 `--report-path` / `--jira-key` 过滤后无匹配时直接失败
