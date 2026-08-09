#!/usr/bin/env python
"""Regenerate the derived sections of the documentation from repository state.

Prose cannot be generated, but the parts of the docs that are *facts about the
repository* can be -- and those are exactly the parts that go stale silently.
Spec counts, statuses, what is accepted, what comes next: all of it is derivable
from spec frontmatter, so none of it should ever be hand-maintained.

Regenerated regions are delimited by:

    <!-- BEGIN GENERATED: <name> -->
    ...
    <!-- END GENERATED: <name> -->

Everything outside those markers is hand-written and never touched.

Run by the pre-commit hook with --write, which re-stages anything it changes, so
a commit can never record a state the docs disagree with. Run with --check in CI
to fail if the two have drifted.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"

STATUS_ORDER = ["Accepted", "In Progress", "Approved", "Draft"]


@dataclass(frozen=True)
class Spec:
    num: int
    title: str
    status: str
    day: int
    deps: list[int]
    path: Path


def load_specs() -> list[Spec]:
    specs: list[Spec] = []
    for path in sorted(SPECS.glob("SPEC-*.md")):
        match = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
        if not match:
            continue
        fields: dict[str, str] = {}
        for line in match.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip()] = value.split("#")[0].strip()
        if "spec" not in fields:
            continue
        specs.append(
            Spec(
                num=int(fields["spec"]),
                title=fields.get("title", "").strip(),
                status=fields.get("status", "Draft").strip(),
                day=int(fields.get("day", 0)),
                deps=[int(x) for x in re.findall(r"\d+", fields.get("depends_on", "[]"))],
                path=path,
            )
        )
    return sorted(specs, key=lambda s: (s.day, s.num))


def doc_files() -> list[Path]:
    """Documents, excluding the index itself -- it describes them, it is not one."""
    return sorted(p for p in (ROOT / "docs").glob("*.md") if p.name != "README.md")


def adr_files() -> list[Path]:
    return sorted((ROOT / "docs" / "adr").glob("*.md"))


# --- section builders --------------------------------------------------------


def build_progress(specs: list[Spec]) -> str:
    counts = {s: sum(1 for x in specs if x.status == s) for s in STATUS_ORDER}
    total = len(specs)
    accepted = counts["Accepted"]
    docs = len(doc_files())
    adrs = len(adr_files())
    src_files = len(list((ROOT / "src").rglob("*.py")))

    bar_width = 28
    filled = round(bar_width * accepted / total) if total else 0
    bar = "█" * filled + "·" * (bar_width - filled)

    nxt = next(
        (s for s in specs if s.status in ("Draft", "Approved", "In Progress")), None
    )
    next_line = (
        f"**Next:** SPEC-{nxt.num:03d} — {nxt.title} (day {nxt.day}, {nxt.status})"
        if nxt
        else "**Next:** all specs accepted"
    )

    rows = "  ·  ".join(f"{name} {counts[name]}" for name in STATUS_ORDER if counts[name])

    return (
        f"`{bar}`  **{accepted} / {total} specs accepted**\n\n"
        f"{rows}\n\n"
        f"{next_line}\n\n"
        f"{docs} documents · {adrs} ADRs · {src_files} implementation files\n"
    )


def build_spec_status(specs: list[Spec]) -> str:
    lines = ["| Day | Spec | Title | Status |", "|---|---|---|---|"]
    for s in specs:
        mark = {"Accepted": "✅", "In Progress": "🔨", "Approved": "📋", "Draft": "📝"}
        lines.append(
            f"| {s.day} | {s.num:03d} | {s.title} | {mark.get(s.status, '')} {s.status} |"
        )
    return "\n".join(lines) + "\n"


def build_doc_counts(specs: list[Spec]) -> str:
    # Deliberately no commit SHA. This runs in pre-commit, before the commit
    # exists, so any SHA here would be the parent's -- permanently off by one,
    # and it would dirty this file on every single commit.
    return f"{len(specs)} specs · {len(doc_files())} documents · {len(adr_files())} ADRs\n"


SECTIONS = {
    "progress": build_progress,
    "spec-status": build_spec_status,
    "doc-counts": build_doc_counts,
}


# --- rewriting ---------------------------------------------------------------


def apply(text: str, name: str, body: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"(<!-- BEGIN GENERATED: {re.escape(name)} -->\n).*?(<!-- END GENERATED: {re.escape(name)} -->)",
        re.S,
    )
    if not pattern.search(text):
        return text, False
    new = pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text)
    return new, new != text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="rewrite files in place")
    parser.add_argument("--check", action="store_true", help="exit 1 if drifted")
    args = parser.parse_args()

    specs = load_specs()
    if not specs:
        print("sync_docs: no specs found", file=sys.stderr)
        return 1

    bodies = {name: fn(specs) for name, fn in SECTIONS.items()}
    changed: list[str] = []

    for path in [ROOT / "README.md", ROOT / "docs" / "README.md", SPECS / "ROADMAP.md"]:
        if not path.exists():
            continue
        text = original = path.read_text(encoding="utf-8")
        for name, body in bodies.items():
            text, _ = apply(text, name, body)
        if text != original:
            changed.append(str(path.relative_to(ROOT)).replace("\\", "/"))
            if args.write:
                path.write_text(text, encoding="utf-8", newline="\n")

    if args.check and changed:
        print("sync_docs: documentation is stale -- run `make sync`:", file=sys.stderr)
        for name in changed:
            print(f"  {name}", file=sys.stderr)
        return 1

    if changed:
        print("sync_docs: updated " + ", ".join(changed))
    else:
        print("sync_docs: up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
