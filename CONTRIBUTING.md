# Contributing

本仓库用于维护安全审计相关 Skills。提交请保持小步、可追溯、可复核。

## 目录与结构

- 每个 Skill 使用独立目录，目录名使用 `kebab-case`
- 每个 Skill 目录必须包含 `SKILL.md`
- 引用材料放在 `references/`
- 脚本放在 `scripts/`
- 避免跨 Skill 复用未声明依赖

## 变更边界

- 优先只修改目标 Skill 所在目录
- 不在无关 PR 中混入安装脚本或其他 Skill 的重构
- 删除或迁移脚本时，必须同步更新对应 `SKILL.md` 的路径说明

## 文档要求

- `SKILL.md` 至少包含：
- `name`
- `description`
- `alwaysApply`
- 触发词（Triggers）或明确入口语句
- 输出边界（例如是否允许写盘）

新增参数或流程时，请在同一 PR 内更新文档与示例。

## 提交前自检

在仓库根目录执行：

```bash
bash -n install.sh
```

如本机安装了 PowerShell：

```powershell
powershell -NoProfile -Command "$null = [System.Management.Automation.Language.Parser]::ParseFile('install.ps1',[ref]$null,[ref]$null)"
```

并确认：
- 新增 Skill 目录含 `SKILL.md`
- 相关路径在文档中可达（尤其 `scripts/*`）
- `git status` 无意外改动

## 提交信息建议

推荐使用前缀：

- `feat(skill-name): ...`
- `fix(skill-name): ...`
- `docs(skill-name): ...`
- `chore: ...`

示例：

```text
docs(jira-dedupe): clarify two-phase dedupe flow
fix(jira-security-report): update script path after migration
```

## Pull Request 要求

- 说明变更目的与影响范围
- 列出是否有 breaking changes
- 给出最小验证步骤（你本地实际执行过的命令）
- 如涉及流程迁移，附旧路径 -> 新路径映射

