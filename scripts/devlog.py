#!/usr/bin/env python
"""Append an entry to DEVLOG.md describing HEAD against its parent.

Run by the post-commit hook. DEVLOG.md is gitignored -- a local working record,
not pushed and not present in a fresh clone.

Commit messages here are deliberately short, so this file carries the detail
instead. Everything in an entry is *derived from the repository*, not from the
commit body: files grouped by area, specs that changed status, documents and
ADRs added by title, and the project state at that commit. The result reads as a
progression rather than a list of paths.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVLOG = ROOT / "DEVLOG.md"

# The empty-tree object, so the first commit diffs against "nothing" rather than
# failing for want of a parent.
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

HEADER = """# DEVLOG

Local working record of what changed in each commit, relative to the one before it.

**This file is gitignored.** Appended automatically by the `post-commit` hook.
Newest entries are at the bottom.
"""

# Ordered: first matching prefix wins.
AREAS: list[tuple[str, str]] = [
    ("specs/", "Specs"),
    ("docs/adr/", "Decision records"),
    ("docs/", "Documentation"),
    ("src/", "Implementation"),
    ("tests/", "Tests"),
    ("scripts/", "Tooling"),
    (".githooks/", "Git hooks"),
    (".github/", "CI"),
    ("data/", "Data"),
    ("site/", "Leaderboard"),
    ("paper/", "Paper"),
]

STATUS_RANK = {"Draft": 0, "Approved": 1, "In Progress": 2, "Accepted": 3}


# Every subprocess call pins UTF-8. Without it Python uses the system codepage
# (cp1252 on Windows), which turns every em-dash in a spec title into mojibake
# and throws outright on some bytes. The docs are full of em-dashes.
_RUN = {"cwd": ROOT, "capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, **_RUN).stdout.strip()


def show(rev: str, path: str) -> str | None:
    """File contents at a revision, or None if it did not exist there."""
    try:
        return subprocess.run(["git", "show", f"{rev}:{path}"], check=True, **_RUN).stdout
    except subprocess.CalledProcessError:
        return None


def area_of(path: str) -> str:
    for prefix, label in AREAS:
        if path.startswith(prefix):
            return label
    return "Project files"


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.split("#")[0].strip()
    return fields


def title_of(text: str) -> str:
    """The document's own H1, minus any 'SPEC-000 — ' or 'ADR 0001 — ' prefix."""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            return re.sub(r"^(SPEC-\d+|ADR \d+)\s*[—-]\s*", "", title)
    return ""


def spec_transitions(parent: str, head: str, changed: list[str]) -> list[str]:
    """Specs whose status moved, e.g. 'SPEC-002  Draft -> Accepted'."""
    moves: list[tuple[int, str, str, str]] = []
    for path in changed:
        if not re.match(r"specs/SPEC-\d+", path):
            continue
        before = show(parent, path)
        after = show(head, path)
        if after is None:
            continue
        old = frontmatter(before).get("status") if before else None
        new = frontmatter(after).get("status")
        if not new or old == new:
            continue
        fm = frontmatter(after)
        num = int(fm.get("spec", "-1"))
        moves.append((num, fm.get("title", ""), old or "new", new))
    moves.sort()
    return [
        f"- **SPEC-{n:03d}** {t} — `{o}` → `{s}`"
        + ("  ✅" if STATUS_RANK.get(s, 0) > STATUS_RANK.get(o, 0) else "")
        for n, t, o, s in moves
    ]


def named_additions(head: str, added: list[str]) -> list[str]:
    """New specs, docs and ADRs listed by title rather than by filename."""
    out: list[str] = []
    for path in sorted(added):
        if not path.endswith(".md"):
            continue
        if not (path.startswith("specs/SPEC-") or path.startswith("docs/")):
            continue
        text = show(head, path)
        if not text:
            continue
        title = title_of(text)
        if title:
            out.append(f"- `{Path(path).name}` — {title}")
    return out


def project_state() -> str:
    counts: dict[str, int] = {}
    total = 0
    for path in sorted((ROOT / "specs").glob("SPEC-*.md")):
        match = re.search(r"^status:\s*(.+?)\s*$", path.read_text(encoding="utf-8"), re.M)
        if match:
            total += 1
            status = match.group(1).split("#")[0].strip()
            counts[status] = counts.get(status, 0) + 1
    if not total:
        return ""
    accepted = counts.get("Accepted", 0)
    breakdown = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    src = len(list((ROOT / "src").rglob("*.py")))
    docs = len([p for p in (ROOT / "docs").glob("*.md") if p.name != "README.md"])
    adrs = len(list((ROOT / "docs" / "adr").glob("*.md")))
    return (
        f"**State after this commit:** {accepted}/{total} specs accepted "
        f"({breakdown}) · {docs} docs · {adrs} ADRs · {src} implementation files"
    )


def main() -> int:
    try:
        sha = git("rev-parse", "--short", "HEAD")
        subject = git("log", "-1", "--pretty=%s")
        when = git("log", "-1", "--pretty=%ad", "--date=format:%Y-%m-%d %H:%M")
        author = git("log", "-1", "--pretty=%an")
    except subprocess.CalledProcessError as exc:
        print(f"devlog: cannot read HEAD ({exc})", file=sys.stderr)
        return 0  # never look like a failed commit; the commit already happened

    try:
        parent = git("rev-parse", "HEAD~1")
        parent_label = git("rev-parse", "--short", "HEAD~1")
    except subprocess.CalledProcessError:
        parent, parent_label = EMPTY_TREE, "(initial)"

    stat = git("diff", "--shortstat", parent, "HEAD") or "no file changes"
    raw = git("diff", "--name-status", parent, "HEAD")

    verb = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}
    changed: list[str] = []
    added: list[str] = []
    grouped: dict[str, list[tuple[str, str]]] = {}

    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        kind = verb.get(parts[0][0], parts[0])
        path = parts[-1]
        changed.append(path)
        if kind == "added":
            added.append(path)
        grouped.setdefault(area_of(path), []).append((kind, path))

    lines = [
        f"\n---\n\n## `{sha}` — {subject}",
        "",
        f"{when} · {author} · against `{parent_label}`",
        "",
        f"**Diff:** {stat.lstrip()}",
        "",
    ]

    moves = spec_transitions(parent, "HEAD", changed)
    if moves:
        lines += ["### Spec status changes", "", *moves, ""]

    new_named = named_additions("HEAD", added)
    if new_named:
        lines += [
            f"### New specs and documents ({len(new_named)})",
            "",
            "<details><summary>show</summary>\n",
            *new_named,
            "\n</details>\n",
        ]

    lines += ["### Files by area", ""]
    for _, label in [*AREAS, ("", "Project files")]:
        entries = grouped.get(label)
        if not entries:
            continue
        tally: dict[str, int] = {}
        for kind, _path in entries:
            tally[kind] = tally.get(kind, 0) + 1
        summary = ", ".join(f"{v} {k}" for k, v in sorted(tally.items()))
        lines.append(f"<details><summary><b>{label}</b> — {summary}</summary>\n")
        lines += [f"- {kind}: `{path}`" for kind, path in sorted(entries, key=lambda x: x[1])]
        lines.append("\n</details>\n")
        grouped.pop(label, None)

    state = project_state()
    if state:
        lines += [state, ""]

    if not DEVLOG.exists():
        DEVLOG.write_text(HEADER, encoding="utf-8", newline="\n")
    with DEVLOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"devlog: appended {sha} ({len(changed)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
