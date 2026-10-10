"""Deterministic WELL checker implemented with the Python standard library only.

Runtime requirement: Python 3.9+ with its standard library. No third-party
packages, package installation, virtual environment, network access, or parser
plugin is required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


CHECKER_ID = "well_check/well_check.py"
CHECKER_VERSION = "5"
RUNTIME_REQUIREMENT = "Python 3.9+ standard library only; no third-party dependencies"
RULES = ("WELL-S001", "WELL-N001", "WELL-N002", "WELL-N003", "WELL-U001")
NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
DEFINITION = re.compile(r"^\s*`([^`]+)`\s+—\s+(.+)$")
ABBREVIATIONS = {"e.g.", "i.e.", "etc.", "vs.", "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Fig.", "No."}
CROSS_DOCUMENT = re.compile(r"(?:\.md(?:#|$)|::)[^\s`]*$")
ATX_HEADING = re.compile(r"^\s{0,3}#{1,6}(?:\s+|$)(.*?)(?:\s+#+\s*)?$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
LIST_ITEM = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(.*)$")
THEMATIC_BREAK = re.compile(r"^\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")
TABLE_DELIMITER_CELL = re.compile(r"^\s*:?-{3,}:?\s*$")
INLINE_CODE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")


@dataclass(frozen=True)
class Finding:
    line: int
    rule: str
    explanation: str


@dataclass(frozen=True)
class Exemption:
    line: int
    rule: str
    kind: str
    explanation: str
    requires_manual_review: bool = False


@dataclass(frozen=True)
class InlineCandidate:
    line: int
    source: str
    prose: str
    codes: list[str]


def _sentence_end(text: str, index: int) -> bool:
    """Recognize a simple sentence boundary without treating common abbreviations as one."""
    char = text[index]
    if char not in ".!?":
        return False
    if char == ".":
        word = text[: index + 1].rsplit(None, 1)[-1] if text[: index + 1].split() else ""
        if word in ABBREVIATIONS or re.fullmatch(r"(?:[A-Za-z]\.){2,}", word):
            return False
        if index and index + 1 < len(text) and text[index - 1].isdigit() and text[index + 1].isdigit():
            return False
    return index + 1 == len(text) or text[index + 1].isspace() or text[index + 1] in "\"')] }"


def _sentences(text: str) -> list[str]:
    start, result = 0, []
    for index in range(len(text)):
        if _sentence_end(text, index):
            sentence = text[start : index + 1].strip()
            if sentence:
                result.append(sentence)
            start = index + 1
    tail = text[start:].strip()
    if tail:
        result.append(tail)
    return result


def _inline_parts(source: str) -> tuple[str, list[str]]:
    """Return prose with simple inline-code spans removed plus those span contents."""
    codes = INLINE_CODE.findall(source)
    prose = INLINE_CODE.sub("", source)
    return prose, codes


def _add_exemption(
    exemptions: list[Exemption],
    line: int,
    kind: str,
    explanation: str,
    *,
    manual: bool = False,
) -> None:
    exemptions.append(Exemption(line, "WELL-U001" if manual else "WELL-S001", kind, explanation, manual))


def _is_table_delimiter(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False
    cells = stripped.strip("|").split("|")
    return len(cells) >= 2 and all(TABLE_DELIMITER_CELL.fullmatch(cell) for cell in cells)


def _looks_like_table_row(line: str) -> bool:
    stripped = line.strip()
    return "|" in stripped and not stripped.startswith(">")


def _is_indented_code(line: str) -> bool:
    return line.startswith("    ") or line.startswith("\t")


def _is_html_block_start(line: str) -> bool:
    stripped = line.lstrip()
    return bool(re.match(r"^<(?:!--|/?[A-Za-z][A-Za-z0-9-]*(?:\s|>|/))", stripped))


def _classify(text: str) -> tuple[list[InlineCandidate], list[InlineCandidate], list[Exemption]]:
    """Classify the WELL-recognized Markdown subset without third-party parsers."""
    lines = text.splitlines()
    prose: list[InlineCandidate] = []
    headings: list[InlineCandidate] = []
    exemptions: list[Exemption] = []
    i = 0
    paragraph_lines: list[str] = []
    paragraph_start = 0

    def flush_paragraph() -> None:
        nonlocal paragraph_lines, paragraph_start
        if not paragraph_lines:
            return
        source = "\n".join(part.strip() for part in paragraph_lines).strip()
        plain, codes = _inline_parts(source)
        if source:
            if len(codes) == 1 and source == f"`{codes[0]}`":
                _add_exemption(exemptions, paragraph_start, "inline-code", "structural syntax is exempt from the sentence rule")
            elif NAME.fullmatch(plain.strip()):
                _add_exemption(exemptions, paragraph_start, "bare-identifier", "structural syntax is exempt from the sentence rule")
            else:
                prose.append(InlineCandidate(paragraph_start, source, plain, codes))
        paragraph_lines = []
        paragraph_start = 0

    # Front matter is recognized only at the document start, which keeps the
    # delimiter rule deterministic without requiring YAML parsing.
    if lines and lines[0].strip() == "---":
        end = None
        for j in range(1, len(lines)):
            if lines[j].strip() in {"---", "..."}:
                end = j
                break
        if end is not None:
            _add_exemption(exemptions, 1, "front-matter", "YAML front matter is structural syntax")
            i = end + 1

    while i < len(lines):
        line = lines[i]
        lineno = i + 1

        if not line.strip():
            flush_paragraph()
            i += 1
            continue

        fence = FENCE.match(line)
        if fence:
            flush_paragraph()
            marker = fence.group(1)
            char, length = marker[0], len(marker)
            i += 1
            while i < len(lines):
                closing = re.match(rf"^\s{{0,3}}{re.escape(char)}{{{length},}}\s*$", lines[i])
                i += 1
                if closing:
                    break
            _add_exemption(exemptions, lineno, "fenced-code", "code block is structural syntax")
            continue

        if line.strip() == "$$":
            flush_paragraph()
            end = None
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "$$":
                    end = j
                    break
            if end is not None:
                _add_exemption(
                    exemptions,
                    lineno,
                    "possible-block-formula",
                    "delimiter-shaped block formula has no WELL-defined machine grammar and requires manual review",
                    manual=True,
                )
                i = end + 1
                continue

        if _is_indented_code(line):
            flush_paragraph()
            start = lineno
            i += 1
            while i < len(lines) and (_is_indented_code(lines[i]) or not lines[i].strip()):
                i += 1
            _add_exemption(exemptions, start, "indented-code", "code block is structural syntax")
            continue

        heading = ATX_HEADING.match(line)
        if heading:
            flush_paragraph()
            source = heading.group(1).strip()
            plain, codes = _inline_parts(source)
            headings.append(InlineCandidate(lineno, source, plain, codes))
            _add_exemption(exemptions, lineno, "heading", "heading is structural syntax")
            i += 1
            continue

        if THEMATIC_BREAK.fullmatch(line):
            flush_paragraph()
            _add_exemption(exemptions, lineno, "thematic-break", "thematic break is structural syntax")
            i += 1
            continue

        if line.lstrip().startswith(">"):
            flush_paragraph()
            quote_lines = []
            start = lineno
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quoted = lines[i].lstrip()[1:]
                if quoted.startswith(" "):
                    quoted = quoted[1:]
                quote_lines.append(quoted)
                i += 1
            content = "\n".join(quote_lines).strip()
            if re.match(r"^(?:example|e\.g\.)\b", content, re.IGNORECASE):
                _add_exemption(exemptions, start, "quoted-example", "explicitly marked quoted example is exempt")
            else:
                _add_exemption(exemptions, start, "blockquote", "blockquote requires explicit example marker or manual review", manual=True)
            continue

        if _is_html_block_start(line):
            flush_paragraph()
            start = lineno
            i += 1
            while i < len(lines) and lines[i].strip():
                i += 1
            _add_exemption(exemptions, start, "unknown-block", "HTML block requires manual review", manual=True)
            continue

        # A pipe-table delimiter establishes table syntax; delimiter lines are
        # structural separators while logical header/body rows receive receipts.
        if i + 1 < len(lines) and _looks_like_table_row(line) and _is_table_delimiter(lines[i + 1]):
            flush_paragraph()
            _add_exemption(exemptions, lineno, "table-row", "table row is structural syntax")
            i += 2
            while i < len(lines) and lines[i].strip() and _looks_like_table_row(lines[i]):
                _add_exemption(exemptions, i + 1, "table-row", "table row is structural syntax")
                i += 1
            continue

        item = LIST_ITEM.match(line)
        if item:
            flush_paragraph()
            content = item.group(1).strip()
            plain, codes = _inline_parts(content)
            if not any(_sentence_end(plain, index) for index in range(len(plain))):
                _add_exemption(exemptions, lineno, "list-fragment", "list item has no sentence punctuation")
            else:
                prose.append(InlineCandidate(lineno, content, plain, codes))
            i += 1
            continue

        if not paragraph_lines:
            paragraph_start = lineno
        paragraph_lines.append(line)
        i += 1

    flush_paragraph()
    return prose, headings, exemptions


def _record_names(
    entries: list[InlineCandidate],
    definitions: dict[str, int],
    codes: list[tuple[str, int]],
    violations: list[Finding],
) -> None:
    for entry in entries:
        definition = DEFINITION.match(entry.source)
        if definition:
            name = definition.group(1)
            if not NAME.fullmatch(name):
                violations.append(Finding(entry.line, "WELL-N001", f"canonical definition `{name}` is not lowercase kebab-case"))
            elif name in definitions:
                violations.append(Finding(entry.line, "WELL-N002", f"canonical definition `{name}` duplicates line {definitions[name]}"))
            else:
                definitions[name] = entry.line
        codes.extend((name, entry.line) for name in entry.codes)


def check_bytes(raw: bytes, artifact: str) -> dict[str, object]:
    digest = hashlib.sha256(raw).hexdigest()
    violations: list[Finding] = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = ""
        violations.append(Finding(1, "WELL-U001", "artifact is not valid UTF-8 Markdown"))

    prose, headings, exemptions = _classify(text)
    definitions: dict[str, int] = {}
    codes: list[tuple[str, int]] = []
    _record_names([*prose, *headings], definitions, codes, violations)

    for entry in prose:
        for sentence in _sentences(entry.prose):
            if not re.search(r"(?<![A-Za-z])because(?![A-Za-z])", sentence):
                violations.append(Finding(entry.line, "WELL-S001", "prose sentence lacks literal `because`"))

    for spelling, line in codes:
        if CROSS_DOCUMENT.search(spelling):
            _add_exemption(
                exemptions,
                line,
                "cross-document-reference",
                f"cross-document reference `{spelling}` has no mechanically defined target grammar",
                manual=True,
            )
            continue
        normalized = spelling.lower().replace("_", "-")
        if spelling != normalized and normalized in definitions:
            violations.append(Finding(line, "WELL-N003", f"canonical reference `{spelling}` is not the exact name `{normalized}`"))

    for exemption in exemptions:
        if exemption.requires_manual_review:
            violations.append(Finding(exemption.line, "WELL-U001", exemption.explanation))

    return {
        "artifact": artifact,
        "artifact_sha256": digest,
        "checker": {"identity": CHECKER_ID, "version": CHECKER_VERSION},
        "applied_rules": list(RULES),
        "violations": [asdict(item) for item in sorted(violations, key=lambda item: (item.line, item.rule, item.explanation))],
        "exemptions": [asdict(item) for item in sorted(exemptions, key=lambda item: (item.line, item.kind, item.explanation))],
        "status": (
            "FAIL"
            if any(item.rule != "WELL-U001" for item in violations)
            else "REVIEW"
            if violations
            else "PASS"
        ),
    }


def check_document(path: Path | str) -> dict[str, object]:
    candidate = Path(path)
    return check_bytes(candidate.read_bytes(), str(candidate))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="check one WELL-governed Markdown document")
    parser.add_argument("artifact", help="Markdown artifact to check")
    args = parser.parse_args(argv)
    try:
        receipt = check_document(args.artifact)
    except OSError as exc:
        receipt = {
            "artifact": args.artifact,
            "checker": {"identity": CHECKER_ID, "version": CHECKER_VERSION},
            "applied_rules": list(RULES),
            "violations": [asdict(Finding(1, "WELL-U001", f"artifact unavailable: {exc.strerror or exc}"))],
            "exemptions": [],
            "status": "FAIL",
        }
    for item in receipt["violations"]:
        print(f"{receipt['artifact']}:{item['line']}: {item['rule']}: {item['explanation']}", file=sys.stderr)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return {"PASS": 0, "FAIL": 1, "REVIEW": 2}[receipt["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
