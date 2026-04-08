#Requires -Version 5.1
<#
.SYNOPSIS
  拉取本仓库最新内容，并将根目录下的 Skill 包同步到本机各 AI 工具的全局 skills 目录（覆盖安装）。

.DESCRIPTION
  自动发现：含 SKILL.md 的子目录视为一个 Skill。
  仅当检测到对应工具的配置主目录存在时，才会创建/写入其 skills 子目录（避免凭空造目录）。
  可用 -ForceTargets 在未检测到工具主目录时仍写入下列默认路径。

.PARAMETER SkipGitPull
  不执行 git pull（离线或仅本地覆盖时使用）。

.PARAMETER DryRun
  只打印将执行的操作，不写入、不拉取。

.PARAMETER ForceTargets
  忽略「工具主目录是否存在」检测，对下列全局 skills 路径全部执行同步（不存在则创建）。
#>
[CmdletBinding()]
param(
  [switch] $SkipGitPull,
  [switch] $DryRun,
  [switch] $ForceTargets
)

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
  if ($PSScriptRoot) { return (Resolve-Path $PSScriptRoot).Path }
  return (Resolve-Path (Split-Path -Parent $MyInvocation.MyCommand.Path)).Path
}

function Get-HomeDir {
  if ($env:HOME) { return $env:HOME.TrimEnd('\', '/') }
  if ($env:USERPROFILE) { return $env:USERPROFILE.TrimEnd('\', '/') }
  throw '无法解析用户主目录（HOME / USERPROFILE）。'
}

function Get-SkillDirectories {
  param([string] $RepoRoot)
  Get-ChildItem -LiteralPath $RepoRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object {
      $_.Name -ne '.git' -and
      (Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') -PathType Leaf)
    }
}

function Get-GlobalSkillTargets {
  param(
    [string] $HomeDir,
    [switch] $Force
  )
  # 元组: (标签, 工具主目录, skills 子路径相对主目录)
  $defs = @(
    @{ Label = 'Cursor'; ToolHome = (Join-Path $HomeDir '.cursor'); SkillsRel = 'skills' },
    @{ Label = 'Codex CLI'; ToolHome = (Join-Path $HomeDir '.codex'); SkillsRel = 'skills' },
    @{ Label = 'Claude Code'; ToolHome = (Join-Path $HomeDir '.claude'); SkillsRel = 'skills' }
  )
  $targets = @()
  foreach ($d in $defs) {
    $skillsPath = Join-Path $d.ToolHome $d.SkillsRel
    if ($Force) {
      $targets += [pscustomobject]@{ Label = $d.Label; Path = $skillsPath; ToolHome = $d.ToolHome }
      continue
    }
    if (Test-Path -LiteralPath $d.ToolHome -PathType Container) {
      $targets += [pscustomobject]@{ Label = $d.Label; Path = $skillsPath; ToolHome = $d.ToolHome }
    }
  }
  return $targets
}

function Sync-SkillsToTarget {
  param(
    [string[]] $SourceSkillPaths,
    [string] $DestRoot,
    [switch] $WhatIf
  )
  if (-not $WhatIf) {
    New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null
  }
  foreach ($src in $SourceSkillPaths) {
    $name = Split-Path -Leaf $src
    $dest = Join-Path $DestRoot $name
    if ($WhatIf) {
      Write-Host "  [WhatIf] 同步: $name -> $dest"
      continue
    }
    if (Test-Path -LiteralPath $dest) {
      Remove-Item -LiteralPath $dest -Recurse -Force
    }
    Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force
  }
}

# --- main ---
$repoRoot = Get-RepoRoot
$homeDir = Get-HomeDir

Write-Host "仓库根目录: $repoRoot"
Write-Host "用户主目录: $homeDir"
Write-Host ""

if (-not $SkipGitPull) {
  if ($DryRun) {
    Write-Host "[DryRun] 将执行: git -C `"$repoRoot`" pull --ff-only"
  } else {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git') -PathType Container)) {
      Write-Warning '当前目录不是 Git 仓库，已跳过 git pull。'
    } else {
      Push-Location $repoRoot
      try {
        git pull --ff-only
        if ($LASTEXITCODE -ne 0) {
          throw "git pull 失败（退出码 $LASTEXITCODE）。可改用 -SkipGitPull 仅同步本地副本。"
        }
      } finally {
        Pop-Location
      }
    }
  }
} else {
  Write-Host '已跳过 git pull（-SkipGitPull）。'
}

$skillDirs = @(Get-SkillDirectories -RepoRoot $repoRoot)
if ($skillDirs.Count -eq 0) {
  throw '未在仓库根目录下找到任何含 SKILL.md 的 Skill 子目录。'
}

Write-Host "将安装的 Skill 包 ($($skillDirs.Count)):"
$skillDirs | ForEach-Object { Write-Host "  - $($_.Name)" }
Write-Host ""

$targets = @(Get-GlobalSkillTargets -HomeDir $homeDir -Force:$ForceTargets)
if ($targets.Count -eq 0) {
  Write-Warning @'
未检测到已安装的工具主目录（.cursor / .codex / .claude）。
请先安装并至少运行过一次对应工具以生成配置目录，或使用 -ForceTargets 强制写入默认全局 skills 路径。
'@
  exit 2
}

foreach ($t in $targets) {
  Write-Host "[$($t.Label)] -> $($t.Path)"
  $paths = @($skillDirs | ForEach-Object { $_.FullName })
  Sync-SkillsToTarget -SourceSkillPaths $paths -DestRoot $t.Path -WhatIf:$DryRun
  if (-not $DryRun) {
    Write-Host "  已完成覆盖安装。"
  }
  Write-Host ""
}

if ($DryRun) {
  Write-Host 'DryRun 结束，未做任何写入。'
} else {
  Write-Host '全部完成。'
}
