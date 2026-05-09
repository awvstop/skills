#!/usr/bin/env python3
"""Semantic lint for SKILL.md files."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted(ROOT.glob("*/SKILL.md"))
REF_RE = re.compile(r"references/([\w\-.]+\.md)")


def lint_one(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    skill_dir = path.parent
    refs = {p.name for p in (skill_dir / "references").glob("*.md")}

    if "Triggers:" not in text:
        errors.append("missing `Triggers:` in frontmatter description block")

    if "## CONTRACT" not in text:
        errors.append("missing `## CONTRACT` section")

    if "输出" not in text:
        errors.append("missing output contract text")

    for ref in sorted(set(REF_RE.findall(text))):
        if ref not in refs:
            errors.append(f"missing reference file: references/{ref}")

    has_bsaf_ref = ".bsaf/" in text
    has_allow_exception = ("仅允许" in text) or ("唯一例外" in text)
    has_readonly_code = "不修改项目代码" in text

    # Accept shared guardrails reference as satisfying readonly constraint
    guardrails_ref = skill_dir / "references" / "guardrails.md"
    if not has_readonly_code and guardrails_ref.exists():
        guardrails_text = guardrails_ref.read_text(encoding="utf-8")
        if "不修改" in guardrails_text:
            has_readonly_code = True
        if "仅允许" in guardrails_text or "唯一允许" in guardrails_text:
            has_allow_exception = True

    if (
        "不得向仓库写入任何文件" in text
        and has_bsaf_ref
        and not has_allow_exception
    ):
        errors.append(
            "contradiction: denies all writes but also references .bsaf without explicit exception"
        )

    if (
        "不向被审计仓库写入" in text
        and has_bsaf_ref
        and not has_allow_exception
    ):
        errors.append(
            "contradiction: forbids writes to audited repo but also references .bsaf without explicit exception"
        )

    if has_bsaf_ref and not has_readonly_code:
        errors.append("uses .bsaf files but missing explicit `不修改项目代码` boundary")

    has_step_or_phase = bool(re.search(r"(Step|Phase)\s*[0-9]", text, re.IGNORECASE))
    has_params_table = "| 参数 |" in text
    if not has_step_or_phase and not has_params_table:
        errors.append("missing execution structure: add Step/Phase markers or 参数 table")

    return errors


def main() -> int:
    if not SKILLS:
        print("No SKILL.md found.")
        return 1

    total_errors = 0
    for skill in SKILLS:
        errs = lint_one(skill)
        if not errs:
            print(f"OK {skill.relative_to(ROOT)}")
            continue
        print(f"FAIL {skill.relative_to(ROOT)}")
        for e in errs:
            print(f"  - {e}")
        total_errors += len(errs)

    if total_errors:
        print(f"\nSemantic lint failed: {total_errors} issue(s).")
        return 1
    print("\nSemantic lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
