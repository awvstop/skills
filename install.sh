#!/usr/bin/env bash
# 拉取本仓库最新内容，并将根目录下的 Skill 包同步到本机各 AI 工具的全局 skills 目录（覆盖安装）。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_GIT_PULL=0
DRY_RUN=0
FORCE_TARGETS=0

usage() {
  echo "用法: $0 [--skip-git-pull] [--dry-run] [--force-targets]" >&2
  echo "  --skip-git-pull   不执行 git pull" >&2
  echo "  --dry-run         只打印将执行的操作" >&2
  echo "  --force-targets   未检测到工具主目录时也写入默认 ~/.cursor/skills 等路径" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-git-pull) SKIP_GIT_PULL=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --force-targets) FORCE_TARGETS=1 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
  shift
done

HOME_DIR="${HOME:-${USERPROFILE:-}}"
if [[ -z "$HOME_DIR" ]]; then
  echo "错误: 无法解析 HOME / USERPROFILE" >&2
  exit 1
fi

echo "仓库根目录: $REPO_ROOT"
echo "用户主目录: $HOME_DIR"
echo

if [[ "$SKIP_GIT_PULL" -eq 0 ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DryRun] 将执行: git -C \"$REPO_ROOT\" pull --ff-only"
  else
    if [[ -d "$REPO_ROOT/.git" ]]; then
      git -C "$REPO_ROOT" pull --ff-only
    else
      echo "警告: 当前目录不是 Git 仓库，已跳过 git pull。" >&2
    fi
  fi
else
  echo "已跳过 git pull（--skip-git-pull）。"
fi

SKILL_DIRS=()
# 兼容 macOS 旧版 Bash，不用 mapfile / 复杂 find
for _cand in "$REPO_ROOT"/*; do
  [[ -d "$_cand" ]] || continue
  _bn="$(basename "$_cand")"
  [[ "$_bn" == ".git" ]] && continue
  [[ -f "$_cand/SKILL.md" ]] && SKILL_DIRS+=("$_cand")
done
unset _cand _bn
if [[ ${#SKILL_DIRS[@]} -eq 0 ]]; then
  echo "错误: 未找到任何含 SKILL.md 的 Skill 子目录。" >&2
  exit 1
fi

echo "将安装的 Skill 包 (${#SKILL_DIRS[@]}):"
for d in "${SKILL_DIRS[@]}"; do echo "  - $(basename "$d")"; done
echo

declare -a TARGETS=()
declare -a LABELS=()

add_target() {
  local label="$1" tool_home="$2" skills_path="$3"
  if [[ "$FORCE_TARGETS" -eq 1 ]]; then
    LABELS+=("$label")
    TARGETS+=("$skills_path")
    return
  fi
  if [[ -d "$tool_home" ]]; then
    LABELS+=("$label")
    TARGETS+=("$skills_path")
  fi
}

add_target "Cursor" "$HOME_DIR/.cursor" "$HOME_DIR/.cursor/skills"
add_target "Codex CLI" "$HOME_DIR/.codex" "$HOME_DIR/.codex/skills"
add_target "Claude Code" "$HOME_DIR/.claude" "$HOME_DIR/.claude/skills"

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "警告: 未检测到已安装的工具主目录（.cursor / .codex / .claude）。" >&2
  echo "请先安装并运行过一次对应工具，或使用 --force-targets。" >&2
  exit 2
fi

sync_one() {
  local dest_root="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    for src in "${SKILL_DIRS[@]}"; do
      local name
      name="$(basename "$src")"
      echo "  [DryRun] 同步: $name -> $dest_root/$name"
    done
    return
  fi
  mkdir -p "$dest_root"
  for src in "${SKILL_DIRS[@]}"; do
    local name
    name="$(basename "$src")"
    rm -rf "$dest_root/$name"
    cp -R "$src" "$dest_root/$name"
  done
}

for i in "${!TARGETS[@]}"; do
  echo "[${LABELS[$i]}] -> ${TARGETS[$i]}"
  sync_one "${TARGETS[$i]}"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    echo "  已完成覆盖安装。"
  fi
  echo
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "DryRun 结束，未做任何写入。"
else
  echo "全部完成。"
fi
