import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "zoom_jira_dedupe.py"
MHTML = ROOT / "tests" / "fixtures" / "sample_zoom.mhtml"
REPORT_DIR = ROOT / "tests" / "reports"


class JiraDedupeCliTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_summary_json_contains_normalized_title(self) -> None:
        proc = self.run_cmd(
            "summary",
            "--mhtml",
            str(MHTML),
            "--report-dir",
            str(REPORT_DIR),
            "--format",
            "json",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["local_reports"])
        self.assertTrue(payload["existing_jira_issues"])
        self.assertIn("normalized_title", payload["local_reports"][0])
        self.assertIn("normalized_title", payload["existing_jira_issues"][0])

    def test_bundle_json_has_candidate_filters(self) -> None:
        proc = self.run_cmd(
            "bundle",
            "--mhtml",
            str(MHTML),
            "--report-dir",
            str(REPORT_DIR),
            "--report-path",
            "sample-report.md",
            "--jira-key",
            "ZOOM-123",
            "--format",
            "json",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["candidate_filters"]["jira_key"], ["ZOOM-123"])
        self.assertEqual(payload["report_count"], 1)
        self.assertEqual(payload["jira_issue_count"], 1)

    def test_summary_strict_fails_on_empty_report_dir(self) -> None:
        empty_dir = ROOT / "tests" / "empty-reports"
        empty_dir.mkdir(exist_ok=True)
        proc = self.run_cmd(
            "summary",
            "--mhtml",
            str(MHTML),
            "--report-dir",
            str(empty_dir),
            "--strict",
            "--format",
            "json",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Strict mode", proc.stderr)


if __name__ == "__main__":
    unittest.main()
