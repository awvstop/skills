# skills

面向安全审计场景的 Codex Skills 集合仓库。  
仓库中的每个子目录（包含 `SKILL.md`）即一个可安装 Skill 包。

## Skills 列表

- `backend-security-audit`: 后端/服务端安全审计（BSAF）
- `frontend-security-audit`: 前端安全审计（CEVF）
- `security-audit-readonly`: 全局只读审计守则
- `verify-security-findings`: 扫描结果复核与误报排除
- `jira-security-report`: 将漏洞整理为 Jira 可落单报告
- `jira-dedupe`: 本地报告与 Jira 已有单去重

## 安装

在仓库根目录执行：

```bash
./install.sh
```

Windows PowerShell：

```powershell
.\install.ps1
```

说明：
- 安装脚本会自动发现包含 `SKILL.md` 的目录并同步到全局 skills 目录
- 默认会先执行 `git pull --ff-only`，可用参数跳过（见下）

## install.sh 参数

- `--skip-git-pull`: 跳过 `git pull`
- `--dry-run`: 只打印即将执行的动作
- `--force-targets`: 即使未检测到工具主目录，也写入默认全局路径

## 维护约定

- 每个 Skill 目录必须包含 `SKILL.md`
- 如有脚本依赖，请在对应 Skill 文档中声明运行方式与输入输出边界
- 提交前建议先本地运行：

```bash
bash -n install.sh
```

```powershell
powershell -NoProfile -Command "$null = [System.Management.Automation.Language.Parser]::ParseFile('install.ps1',[ref]$null,[ref]$null)"
```

## jira-dedupe 快速用法

前提：
- Jira 已有单导出文件：`~/Zoom.mhtml`
- 本地报告目录：`<repo>/report`

第一阶段（候选筛选）：

```bash
python jira-dedupe/scripts/zoom_jira_dedupe.py summary \
  --mhtml ~/Zoom.mhtml \
  --report-dir /abs/path/to/repo/report \
  --format markdown \
  --strict
```

第二阶段（候选全文比对材料）：

```bash
python jira-dedupe/scripts/zoom_jira_dedupe.py bundle \
  --mhtml ~/Zoom.mhtml \
  --report-dir /abs/path/to/repo/report \
  --report-path report-a.md \
  --jira-key ZOOM-123 \
  --format markdown \
  --strict
```

## 许可证

当前仓库未声明 License；如需开源分发，建议补充 `LICENSE` 文件并在此更新。
