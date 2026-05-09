#!/usr/bin/env python3
"""Validate shared markdown references can be resolved on current filesystem."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REL_MD_RE = re.compile(r"^(?:\./|\../).+\.md$")
CHECKS = [
    ("backend-security-audit/references/guardrails.md", "只读约束"),
    ("frontend-security-audit/references/guardrails.md", "只读约束"),
    ("security-audit-readonly/references/guardrails.md", "只读约束"),
    ("verify-security-findings/references/guardrails.md", "只读约束"),
    (
        "jira-security-report/references/severity-vocabulary-mapping.md",
        "严重性对照",
    ),
    (
        "security-audit-readonly/references/severity-vocabulary-mapping.md",
        "严重性对照",
    ),
    (
        "verify-security-findings/references/severity-vocabulary-mapping.md",
        "严重性对照",
    ),
]


def resolve_content(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    line = text.strip()
    if "\n" in text or not REL_MD_RE.fullmatch(line):
        return text
    target = (path.parent / line).resolve()
    if target.exists():
        return target.read_text(encoding="utf-8")
    return text


def main() -> int:
    errors = 0
    for rel, expected in CHECKS:
        p = ROOT / rel
        if not p.exists():
            print(f"FAIL missing: {rel}")
            errors += 1
            continue
        content = resolve_content(p)
        if expected not in content:
            print(f"FAIL unresolved or invalid content: {rel}")
            errors += 1
            continue
        print(f"OK {rel}")
    if errors:
        print(f"\nShared ref validation failed: {errors} issue(s).")
        return 1
    print("\nShared ref validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
