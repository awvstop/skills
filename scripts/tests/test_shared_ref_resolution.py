from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_shared_refs import resolve_content
from scripts.skill_semantic_lint import resolve_ref_text


class SharedRefResolutionTests(unittest.TestCase):
    def test_relative_md_path_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shared = root / "_shared" / "doc.md"
            shared.parent.mkdir(parents=True, exist_ok=True)
            shared.write_text("expected body", encoding="utf-8")

            ref = root / "skill" / "references" / "doc.md"
            ref.parent.mkdir(parents=True, exist_ok=True)
            ref.write_text("../../_shared/doc.md", encoding="utf-8")

            self.assertEqual(resolve_ref_text(ref), "expected body")
            self.assertEqual(resolve_content(ref), "expected body")

    def test_single_line_non_relative_md_is_not_treated_as_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = root / "skill" / "references" / "doc.md"
            ref.parent.mkdir(parents=True, exist_ok=True)
            ref.write_text("just-notes.md", encoding="utf-8")

            self.assertEqual(resolve_ref_text(ref), "just-notes.md")
            self.assertEqual(resolve_content(ref), "just-notes.md")


if __name__ == "__main__":
    unittest.main()
