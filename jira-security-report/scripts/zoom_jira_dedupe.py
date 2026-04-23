#!/usr/bin/env python3
"""
Prepare Jira dedupe review material for an LLM.

This script only extracts information. It does not decide whether reports are
duplicates. The LLM should compare the extracted Jira issues against local
report markdown files in the conversation.

Safety rule:
- Outputs default to stdout.
- If --out is used, the output path must stay outside the audited project root.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path


ISSUE_SPLIT_RE = re.compile(r'<h3 class="formtitle">', re.IGNORECASE)
ISSUE_META_RE = re.compile(
    r"\[(ZOOM-\d+)\].*?<a[^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
DESCRIPTION_RE = re.compile(
    r'<td id="descriptionArea">(.*?)</td>',
    re.IGNORECASE | re.DOTALL,
)
FIELD_ROW_RE = re.compile(
    r"<tr>\s*<td\b[^>]*>\s*<b>\s*(.*?)\s*</b>\s*</td>\s*"
    r"<td\b(?=[^>]*\bclass=[\"'][^\"']*\bvalue\b)[^>]*>(.*?)</td>\s*</tr>",
    re.IGNORECASE | re.DOTALL,
)
MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$", re.MULTILINE)
MARKDOWN_SECTION_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)
WHITESPACE_RE = re.compile(r"\s+")
CWE_TEXT_RE = re.compile(r"\bCWE-\d+\b(?:\s*\([^)]+\))?", re.IGNORECASE)
JIRA_FIELD_ALLOWLIST = {
    "Bug Type",
    "CWE",
    "Zoom Module",
    "Bug From",
    "CVSS Severity",
    "Vulnerability Exception Type",
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"br", "p", "div", "li", "tr", "td", "h1", "h2", "h3"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li", "tr", "td", "h1", "h2", "h3"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def get_text(self) -> str:
        text = "".join(self._chunks)
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)


@dataclass
class JiraIssue:
    issue_key: str
    title: str
    vulnerability_type: str
    fields: dict[str, str]
    description_text: str


@dataclass
class ReportDoc:
    path: str
    title: str
    vulnerability_type: str
    content: str


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def html_to_text(value: str) -> str:
    parser = TextExtractor()
    parser.feed(value)
    return parser.get_text()


def normalize_field_label(value: str) -> str:
    return html_to_text(value).rstrip(":").strip()


def extract_issue_fields(segment: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for label_html, value_html in FIELD_ROW_RE.findall(segment):
        label = normalize_field_label(label_html)
        if label not in JIRA_FIELD_ALLOWLIST:
            continue
        value = compact_text(html_to_text(value_html), 1000)
        if value:
            fields[label] = value
    return fields


def load_main_html(mhtml_path: Path) -> str:
    message = BytesParser(policy=policy.default).parsebytes(mhtml_path.read_bytes())
    html_parts = [
        part for part in message.walk() if part.get_content_type() == "text/html"
    ]
    if not html_parts:
        raise ValueError(f"No text/html part found in {mhtml_path}")
    return html_parts[0].get_content()


def extract_issues(mhtml_path: Path) -> list[JiraIssue]:
    html = load_main_html(mhtml_path)
    segments = ISSUE_SPLIT_RE.split(html)
    issues: list[JiraIssue] = []
    for segment in segments[1:]:
        meta_match = ISSUE_META_RE.search(segment)
        desc_match = DESCRIPTION_RE.search(segment)
        if not meta_match or not desc_match:
            continue
        title = html_to_text(meta_match.group(2).strip()).strip()
        fields = extract_issue_fields(segment)
        description_text = html_to_text(desc_match.group(1).strip())
        vulnerability_type = fields.get("CWE", "") or infer_vulnerability_type_from_text(
            description_text
        )
        issues.append(
            JiraIssue(
                issue_key=meta_match.group(1).strip(),
                title=title,
                vulnerability_type=vulnerability_type,
                fields=fields,
                description_text=description_text,
            )
        )
    if not issues:
        raise ValueError(f"No Jira issues extracted from {mhtml_path}")
    return issues


def get_markdown_title(content: str, fallback: str) -> str:
    match = MARKDOWN_HEADING_RE.search(content)
    if match:
        return match.group(1).strip()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return fallback


def get_markdown_sections(content: str) -> dict[str, str]:
    matches = list(MARKDOWN_SECTION_RE.finditer(content))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        key = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[key] = content[start:end].strip()
    return sections


def get_report_vulnerability_type(content: str) -> str:
    sections = get_markdown_sections(content)
    for heading, body in sections.items():
        normalized = heading.lower()
        if "漏洞类型" in heading or "vulnerability type" in normalized:
            return compact_text(body, 1000)
    return ""


def compact_text(value: str, max_chars: int) -> str:
    normalized = WHITESPACE_RE.sub(" ", value).strip()
    if max_chars <= 0 or len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rstrip() + " ...[truncated]"


def infer_vulnerability_type_from_text(value: str) -> str:
    seen: set[str] = set()
    cwes: list[str] = []
    for match in CWE_TEXT_RE.finditer(value):
        cwe = match.group(0).strip()
        key = cwe.lower()
        if key in seen:
            continue
        seen.add(key)
        cwes.append(cwe)
    return "; ".join(cwes[:8])


def load_reports(report_dir: Path, max_report_chars: int) -> list[ReportDoc]:
    reports: list[ReportDoc] = []
    for path in sorted(report_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8", errors="replace")
        reports.append(
            ReportDoc(
                path=str(path),
                title=get_markdown_title(content, path.stem),
                vulnerability_type=get_report_vulnerability_type(content),
                content=compact_text(content, max_report_chars),
            )
        )
    return reports


def issue_to_dict(issue: JiraIssue, max_description_chars: int) -> dict:
    return {
        "issue_key": issue.issue_key,
        "title": issue.title,
        "vulnerability_type": issue.vulnerability_type,
        "fields": issue.fields,
        "description_text": compact_text(issue.description_text, max_description_chars),
    }


def report_to_dict(report: ReportDoc) -> dict:
    return {
        "path": report.path,
        "title": report.title,
        "vulnerability_type": report.vulnerability_type,
        "content": report.content,
    }


def issue_summary_to_dict(issue: JiraIssue) -> dict:
    return {
        "issue_key": issue.issue_key,
        "title": issue.title,
        "vulnerability_type": issue.vulnerability_type,
    }


def report_summary_to_dict(report: ReportDoc) -> dict:
    return {
        "path": report.path,
        "title": report.title,
        "vulnerability_type": report.vulnerability_type,
    }


def render_markdown_summary(payload: dict) -> str:
    lines: list[str] = []
    lines.append("# Jira Dedupe Candidate Summary")
    lines.append("")
    lines.append(
        "The script only extracted titles and vulnerability types. The LLM must identify candidate pairs only, not final duplicates."
    )
    lines.append("")
    lines.append("## Local Reports")
    for index, report in enumerate(payload["local_reports"], start=1):
        lines.append(f"### Report {index}")
        lines.append(f"Path: `{report['path']}`")
        lines.append(f"Title: {report['title']}")
        lines.append(f"Vulnerability Type: {report.get('vulnerability_type') or '(missing)'}")
        lines.append("")
    lines.append("## Existing Jira Issues")
    for issue in payload["existing_jira_issues"]:
        lines.append(f"### {issue['issue_key']}")
        lines.append(f"Title: {issue['title']}")
        lines.append(f"Vulnerability Type / CWE: {issue.get('vulnerability_type') or '(missing)'}")
        lines.append("")
    lines.append("## LLM Task")
    lines.append(
        "Find candidate report/Jira pairs that need full-text verification. Be recall-oriented: include plausible candidates when title/module/object/vulnerability type overlap. Do not mark final duplicates in this stage."
    )
    return "\n".join(lines).rstrip() + "\n"


def render_markdown_bundle(payload: dict) -> str:
    lines: list[str] = []
    lines.append("# Jira Dedupe Review Material")
    lines.append("")
    lines.append("The script only extracted material. The LLM must decide duplicates.")
    lines.append("")
    lines.append("## Local Reports To Check")
    for index, report in enumerate(payload["local_reports"], start=1):
        lines.append(f"### Report {index}: {report['title']}")
        lines.append(f"Path: `{report['path']}`")
        if report.get("vulnerability_type"):
            lines.append(f"Vulnerability Type: {report['vulnerability_type']}")
        lines.append("")
        lines.append(report["content"])
        lines.append("")
    lines.append("## Existing Jira Issues")
    for issue in payload["existing_jira_issues"]:
        lines.append(f"### {issue['issue_key']}: {issue['title']}")
        if issue.get("vulnerability_type"):
            lines.append(f"Vulnerability Type / CWE: {issue['vulnerability_type']}")
        extra_fields = {
            key: value
            for key, value in issue.get("fields", {}).items()
            if key != "CWE"
        }
        if extra_fields:
            field_text = "; ".join(f"{key}: {value}" for key, value in extra_fields.items())
            lines.append(f"Jira Fields: {field_text}")
        lines.append("")
        lines.append(issue["description_text"])
        lines.append("")
    lines.append("## LLM Task")
    lines.append(
        "Compare each local report against existing Jira issues. Return confirmed duplicates, possible duplicates, and reports with no match. Explain the evidence briefly."
    )
    return "\n".join(lines).rstrip() + "\n"


def filter_reports(reports: list[ReportDoc], selected_paths: list[Path] | None) -> list[ReportDoc]:
    if not selected_paths:
        return reports
    selected = {str(path.resolve()).lower() for path in selected_paths}
    selected_names = {path.name.lower() for path in selected_paths}
    return [
        report
        for report in reports
        if str(Path(report.path).resolve()).lower() in selected
        or Path(report.path).name.lower() in selected_names
    ]


def filter_issues(issues: list[JiraIssue], selected_keys: list[str] | None) -> list[JiraIssue]:
    if not selected_keys:
        return issues
    selected = {key.upper() for key in selected_keys}
    return [issue for issue in issues if issue.issue_key.upper() in selected]


def ensure_output_is_external(output_path: Path, project_root: Path | None) -> None:
    if project_root is None:
        return
    output_resolved = output_path.resolve()
    root_resolved = project_root.resolve()
    try:
        output_resolved.relative_to(root_resolved)
    except ValueError:
        return
    raise ValueError(
        f"Refusing to write output into project root: {output_resolved} is inside {root_resolved}"
    )


def write_or_print(text: str, output_path: Path | None, project_root: Path | None) -> None:
    if output_path is None:
        sys.stdout.write(text)
        return
    ensure_output_is_external(output_path, project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def command_extract(args: argparse.Namespace) -> int:
    issues = extract_issues(args.mhtml)
    payload = {
        "source": str(args.mhtml),
        "count": len(issues),
        "issues": [
            issue_to_dict(issue, args.max_description_chars) for issue in issues
        ],
    }
    text = (
        render_markdown_bundle({"local_reports": [], "existing_jira_issues": payload["issues"]})
        if args.format == "markdown"
        else json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    write_or_print(text, args.out, args.project_root)
    return 0


def command_summary(args: argparse.Namespace) -> int:
    issues = extract_issues(args.mhtml)
    reports = load_reports(args.report_dir, max_report_chars=1)
    payload = {
        "source_mhtml": str(args.mhtml),
        "report_dir": str(args.report_dir),
        "jira_issue_count": len(issues),
        "report_count": len(reports),
        "local_reports": [report_summary_to_dict(report) for report in reports],
        "existing_jira_issues": [issue_summary_to_dict(issue) for issue in issues],
    }
    text = (
        render_markdown_summary(payload)
        if args.format == "markdown"
        else json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    write_or_print(text, args.out, args.project_root or args.report_dir.parent)
    return 0


def command_bundle(args: argparse.Namespace) -> int:
    issues = extract_issues(args.mhtml)
    reports = load_reports(args.report_dir, args.max_report_chars)
    issues = filter_issues(issues, args.jira_key)
    reports = filter_reports(reports, args.report_path)
    payload = {
        "source_mhtml": str(args.mhtml),
        "report_dir": str(args.report_dir),
        "jira_issue_count": len(issues),
        "report_count": len(reports),
        "local_reports": [report_to_dict(report) for report in reports],
        "existing_jira_issues": [
            issue_to_dict(issue, args.max_description_chars) for issue in issues
        ],
    }
    text = (
        render_markdown_bundle(payload)
        if args.format == "markdown"
        else json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    write_or_print(text, args.out, args.project_root or args.report_dir.parent)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Jira dedupe review material from Zoom.mhtml and report markdown files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract existing Jira issue titles and descriptions from Zoom.mhtml.",
    )
    extract_parser.add_argument("--mhtml", type=Path, required=True)
    extract_parser.add_argument("--out", type=Path)
    extract_parser.add_argument("--project-root", type=Path)
    extract_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    extract_parser.add_argument("--max-description-chars", type=int, default=4000)
    extract_parser.set_defaults(func=command_extract)

    summary_parser = subparsers.add_parser(
        "summary",
        help="Extract only titles and vulnerability types for LLM candidate screening.",
    )
    summary_parser.add_argument("--mhtml", type=Path, required=True)
    summary_parser.add_argument("--report-dir", type=Path, required=True)
    summary_parser.add_argument("--out", type=Path)
    summary_parser.add_argument("--project-root", type=Path)
    summary_parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    summary_parser.set_defaults(func=command_summary)

    bundle_parser = subparsers.add_parser(
        "bundle",
        help="Extract local reports and existing Jira issues into one LLM review bundle.",
    )
    bundle_parser.add_argument("--mhtml", type=Path, required=True)
    bundle_parser.add_argument("--report-dir", type=Path, required=True)
    bundle_parser.add_argument("--out", type=Path)
    bundle_parser.add_argument("--project-root", type=Path)
    bundle_parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    bundle_parser.add_argument("--max-description-chars", type=int, default=4000)
    bundle_parser.add_argument("--max-report-chars", type=int, default=8000)
    bundle_parser.add_argument(
        "--report-path",
        type=Path,
        action="append",
        help="Limit full-text bundle to a candidate report path or filename. Repeatable.",
    )
    bundle_parser.add_argument(
        "--jira-key",
        action="append",
        help="Limit full-text bundle to a candidate Jira issue key such as ZOOM-123. Repeatable.",
    )
    bundle_parser.set_defaults(func=command_bundle)

    return parser


def main() -> int:
    configure_stdout()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
