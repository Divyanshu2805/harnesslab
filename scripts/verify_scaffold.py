#!/usr/bin/env python
"""Structural verification of the spec system and documentation.

Enforces the claims made in specs/ROADMAP.md and the plan's verification
section. Run by `make check` and by CI, because "checked mechanically, not by
eye" is only true if something actually checks it.

The ordering invariant here is the one that matters: an earlier revision of the
plan scheduled the power analysis (029) on Day 18 while the bootstrap it
simulates over (024) landed on Day 25 -- a dependency that resolved on paper and
was unrunnable in practice. That class of error is invisible to a dependency
graph alone; it needs the schedule.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
DOCS = ROOT / "docs"

# Docs that must exist and be substantive before implementation begins.
REQUIRED_DOCS = [
    "ARCHITECTURE.md",
    "METHODOLOGY.md",
    "EXPERIMENT_DESIGN.md",
    "COST_MODEL.md",
    "CONTAMINATION.md",
    "PREREGISTRATION.md",
    "PROVIDERS.md",
    "TOKEN_BUDGET.md",
    "PUBLICATION.md",
    "README.md",
]

FULL_SPECS = range(0, 7)  # 000-006 are written in full; the rest are stubs.
N_ADRS = 11
MIN_DOC_CHARS = 1500

# Same-day dependency pairs that are deliberate. Within a day, ROADMAP row order
# is build order. Anything not listed here is reported so it gets a decision.
ALLOWED_SAME_DAY: set[tuple[int, int]] = {(1, 0), (23, 22)}


def parse_frontmatter(path: Path) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.split("#")[0].strip()
    return fields


def main() -> int:
    failures: list[str] = []
    notes: list[str] = []

    # -- specs: frontmatter, dependencies, schedule ordering, required sections
    specs: dict[int, dict[str, object]] = {}
    for path in sorted(SPECS.glob("SPEC-*.md")):
        fm = parse_frontmatter(path)
        if not fm.get("spec"):
            failures.append(f"{path.name}: missing frontmatter 'spec'")
            continue
        specs[int(fm["spec"])] = {
            "path": path,
            "day": int(fm["day"]),
            "deps": [int(x) for x in re.findall(r"\d+", fm.get("depends_on", "[]"))],
            "text": path.read_text(encoding="utf-8"),
        }

    for num, spec in sorted(specs.items()):
        day = spec["day"]
        for dep in spec["deps"]:  # type: ignore[union-attr]
            if dep not in specs:
                failures.append(f"SPEC-{num:03d}: depends on {dep:03d}, which does not exist")
                continue
            dep_day = specs[dep]["day"]
            if dep_day > day:
                failures.append(
                    f"ORDERING: SPEC-{num:03d} (day {day}) depends on "
                    f"SPEC-{dep:03d} scheduled LATER (day {dep_day})"
                )
            elif dep_day == day and (num, dep) not in ALLOWED_SAME_DAY:
                failures.append(
                    f"ORDERING: SPEC-{num:03d} depends on SPEC-{dep:03d} on the same "
                    f"day ({day}) and is not in ALLOWED_SAME_DAY"
                )

        text = str(spec["text"])
        if "## Scope" not in text:
            failures.append(f"SPEC-{num:03d}: no '## Scope' section")
        if not re.search(r"\*\*AC-1\.", text):
            failures.append(f"SPEC-{num:03d}: no numbered acceptance criteria")
        if num in FULL_SPECS and "## Interface contract" not in text:
            failures.append(f"SPEC-{num:03d}: declared full but has no interface contract")

    # -- cycle detection
    resolved: set[int] = set()

    def visit(node: int, stack: tuple[int, ...]) -> None:
        if node in stack:
            path = " -> ".join(f"{n:03d}" for n in (*stack, node))
            failures.append(f"CYCLE: {path}")
            return
        if node in resolved:
            return
        for dep in specs.get(node, {}).get("deps", []):  # type: ignore[union-attr]
            if dep in specs:
                visit(dep, (*stack, node))
        resolved.add(node)

    for node in specs:
        visit(node, ())

    # -- documentation present and substantive
    for name in REQUIRED_DOCS:
        path = DOCS / name
        if not path.exists():
            failures.append(f"docs/{name}: MISSING")
        elif len(path.read_text(encoding="utf-8")) < MIN_DOC_CHARS:
            failures.append(f"docs/{name}: under {MIN_DOC_CHARS} chars -- placeholder?")

    for i in range(1, N_ADRS + 1):
        if not list((DOCS / "adr").glob(f"{i:04d}-*.md")):
            failures.append(f"docs/adr/{i:04d}-*.md: MISSING")

    # -- every provider claim carries a fetch date and a source
    providers = (DOCS / "PROVIDERS.md").read_text(encoding="utf-8")
    if len(re.findall(r"\d{4}-\d{2}-\d{2}", providers)) < 8:
        failures.append("PROVIDERS.md: fewer than 8 dated rows")
    if "http" not in providers:
        failures.append("PROVIDERS.md: no source URLs")

    # -- no unfilled result placeholders outside the README
    markdown = [*DOCS.rglob("*.md"), *SPECS.glob("*.md")]
    for path in markdown:
        for match in re.finditer(r"\[[XYNMKTFP]\]", path.read_text(encoding="utf-8")):
            failures.append(f"{path.relative_to(ROOT)}: result placeholder {match.group(0)}")

    # -- no dangling internal links
    for path in [*markdown, ROOT / "README.md"]:
        for match in re.finditer(r"\]\(([^)#:]+\.md)[^)]*\)", path.read_text(encoding="utf-8")):
            if not (path.parent / match.group(1)).resolve().exists():
                failures.append(f"{path.relative_to(ROOT)}: dangling link -> {match.group(1)}")

    # -- every referenced image exists
    for path in [*markdown, ROOT / "README.md"]:
        text = path.read_text(encoding="utf-8")
        refs = [*re.findall(r'<img[^>]+src="([^"]+)"', text),
                *re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", text)]
        for src in refs:
            if src.startswith(("http://", "https://", "data:")):
                continue
            if not (path.parent / src).resolve().exists():
                failures.append(f"{path.relative_to(ROOT)}: missing image -> {src}")

    # -- every SVG parses. GitHub renders SVG only as a referenced file, so a
    #    malformed one fails silently in the browser rather than loudly here.
    for svg in sorted((ROOT / "docs" / "assets").glob("*.svg")):
        try:
            ElementTree.parse(svg)
        except ElementTree.ParseError as exc:
            failures.append(f"{svg.relative_to(ROOT)}: malformed SVG ({exc})")

    # -- no ASCII box-drawing art. Diagrams are SVG (layout) or Mermaid (graphs);
    #    GitHub strips inline <svg>, so SVG must live in docs/assets and be
    #    referenced. Ranges are box-drawing U+2500-257F plus arrow triangles --
    #    deliberately NOT the em-dash U+2014, which the prose uses everywhere.
    box_art = re.compile(r"[─-╿▲▶▼◀]")
    for path in [*markdown, ROOT / "README.md"]:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if box_art.search(line):
                failures.append(
                    f"{path.relative_to(ROOT)}:{lineno}: ASCII box-drawing art -- "
                    f"use an SVG in docs/assets or a ```mermaid block"
                )

    print(f"specs: {len(specs)} ({min(specs):03d}-{max(specs):03d})   docs: {len(REQUIRED_DOCS)}   adrs: {N_ADRS}")
    for note in notes:
        print(f"note  {note}")
    if failures:
        print()
        for failure in failures:
            print(f"FAIL  {failure}")
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("All structural checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
