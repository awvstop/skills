Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Add-Result {
  param(
    [string] $Level,
    [string] $Message
  )
  $script:Results += [pscustomobject]@{
    Level = $Level
    Message = $Message
  }
}

function Assert-Path {
  param(
    [string] $Path,
    [string] $Label
  )
  if (Test-Path -LiteralPath $Path) {
    Add-Result -Level "PASS" -Message "$Label exists: $Path"
    return $true
  }
  Add-Result -Level "FAIL" -Message "$Label missing: $Path"
  return $false
}

function Test-LinkTarget {
  param(
    [string] $Path,
    [string] $ExpectedSuffix
  )
  if (-not (Test-Path -LiteralPath $Path)) {
    Add-Result -Level "FAIL" -Message "Reference missing: $Path"
    return
  }

  $item = Get-Item -LiteralPath $Path -Force
  $linkTarget = $null
  if ($item.PSObject.Properties.Name -contains "LinkTarget") {
    $linkTarget = $item.LinkTarget
  }

  if ($null -eq $linkTarget -or $linkTarget.Count -eq 0) {
    $raw = Get-Content -LiteralPath $Path -Raw
    $line = $raw.Trim()
    if ($line -match '\.md$' -and -not ($line -match "`n")) {
      $target = Resolve-Path -LiteralPath (Join-Path (Split-Path -Parent $Path) $line) -ErrorAction SilentlyContinue
      if ($target) {
        Add-Result -Level "PASS" -Message "Reference file (non-symlink) resolves: $Path -> $target"
      } else {
        Add-Result -Level "WARN" -Message "Reference file target missing: $Path -> $line"
      }
    } else {
      Add-Result -Level "WARN" -Message "Not a filesystem symlink (may be copied file): $Path"
    }
    return
  }

  $normalized = ($linkTarget -join ";")
  $normalizedCanonical = $normalized.Replace('\', '/')
  $expectedCanonical = $ExpectedSuffix.Replace('\', '/')
  if ($normalizedCanonical -like "*$expectedCanonical") {
    Add-Result -Level "PASS" -Message "Symlink OK: $Path -> $normalized"
  } else {
    Add-Result -Level "WARN" -Message "Symlink target unexpected: $Path -> $normalized"
  }
}

function Test-GitIndexSymlink {
  param(
    [string] $RepoRoot,
    [string] $Path
  )
  $line = git -C $RepoRoot ls-files -s -- $Path
  if (-not $line) {
    Add-Result -Level "FAIL" -Message "Not tracked in git index: $Path"
    return
  }
  if ($line -match "^120000\s") {
    Add-Result -Level "PASS" -Message "Git index symlink mode OK: $Path"
  } else {
    Add-Result -Level "WARN" -Message "Git index mode is not symlink for $Path : $line"
  }
}

$script:Results = @()
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "Repo root: $repoRoot"

$gitStatus = git -C $repoRoot status --short --branch
if ($gitStatus -match "^\#\#") {
  Add-Result -Level "PASS" -Message ("Git status: " + ($gitStatus -split "`n")[0].Trim())
}
if ($gitStatus -match "^\s*[MADRCU\?\!]" -or ($gitStatus -split "`n").Count -gt 1) {
  Add-Result -Level "WARN" -Message "Worktree has local changes or untracked files."
} else {
  Add-Result -Level "PASS" -Message "Worktree clean."
}

Assert-Path -Path (Join-Path $repoRoot "_shared\guardrails.md") -Label "_shared guardrails" | Out-Null
Assert-Path -Path (Join-Path $repoRoot "_shared\severity-vocabulary-mapping.md") -Label "_shared severity mapping" | Out-Null
Assert-Path -Path (Join-Path $repoRoot ".github\workflows\skills-ci.yml") -Label "CI workflow" | Out-Null
Assert-Path -Path (Join-Path $repoRoot "scripts\skill_semantic_lint.py") -Label "semantic lint script" | Out-Null

$skillFiles = Get-ChildItem -LiteralPath $repoRoot -Directory |
  ForEach-Object { Join-Path $_.FullName "SKILL.md" } |
  Where-Object { Test-Path -LiteralPath $_ }

if ($skillFiles.Count -gt 0) {
  Add-Result -Level "PASS" -Message "Detected SKILL.md files: $($skillFiles.Count)"
} else {
  Add-Result -Level "FAIL" -Message "No SKILL.md found under root subdirectories."
}

$guardrailRefs = @(
  "backend-security-audit/references/guardrails.md",
  "frontend-security-audit/references/guardrails.md",
  "security-audit-readonly/references/guardrails.md",
  "verify-security-findings/references/guardrails.md"
)
foreach ($ref in $guardrailRefs) {
  $full = Join-Path $repoRoot ($ref -replace "/", "\")
  Test-LinkTarget -Path $full -ExpectedSuffix "_shared/guardrails.md"
  Test-GitIndexSymlink -RepoRoot $repoRoot -Path $ref
}

$severityRefs = @(
  "jira-security-report/references/severity-vocabulary-mapping.md",
  "security-audit-readonly/references/severity-vocabulary-mapping.md",
  "verify-security-findings/references/severity-vocabulary-mapping.md"
)
foreach ($ref in $severityRefs) {
  $full = Join-Path $repoRoot ($ref -replace "/", "\")
  Test-LinkTarget -Path $full -ExpectedSuffix "_shared/severity-vocabulary-mapping.md"
  Test-GitIndexSymlink -RepoRoot $repoRoot -Path $ref
}

$ciPath = Join-Path $repoRoot ".github\workflows\skills-ci.yml"
$ciText = Get-Content -LiteralPath $ciPath -Raw
if ($ciText -match "scripts/skill_semantic_lint.py") {
  Add-Result -Level "PASS" -Message "CI includes semantic lint step."
} else {
  Add-Result -Level "FAIL" -Message "CI missing semantic lint step."
}

$installSh = Get-Content -LiteralPath (Join-Path $repoRoot "install.sh") -Raw
$installPs1 = Get-Content -LiteralPath (Join-Path $repoRoot "install.ps1") -Raw
if ($installSh -match "_shared") {
  Add-Result -Level "PASS" -Message "install.sh includes _shared sync."
} else {
  Add-Result -Level "FAIL" -Message "install.sh missing _shared sync logic."
}
if ($installPs1 -match "_shared") {
  Add-Result -Level "PASS" -Message "install.ps1 includes _shared sync."
} else {
  Add-Result -Level "FAIL" -Message "install.ps1 missing _shared sync logic."
}

$pass = @($Results | Where-Object { $_.Level -eq "PASS" }).Count
$warn = @($Results | Where-Object { $_.Level -eq "WARN" }).Count
$fail = @($Results | Where-Object { $_.Level -eq "FAIL" }).Count

Write-Host ""
foreach ($r in $Results) {
  Write-Host "[$($r.Level)] $($r.Message)"
}
Write-Host ""
Write-Host "Summary: PASS=$pass WARN=$warn FAIL=$fail"

if ($fail -gt 0) {
  exit 1
}
