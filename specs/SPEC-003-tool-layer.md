---
spec: 003
title: Tool layer over the Store-backed environment
status: Draft
depends_on: [002]
day: 3
---

# SPEC-003 — Tool layer over the Store-backed environment

## Motivation

The tools are the agent's entire interface to the world, so they are also the
experiment's main source of unwanted variance. Three properties matter more than
breadth:

1. **Identical across harnesses and models.** If `react` saw a different
   `read_file` than `plan_execute`, the harness comparison would be measuring
   the tools. Every harness gets the same tool objects.
2. **No side effect escapes the sample.** All state lives in the per-sample
   Store. A tool that could touch the real filesystem would make concurrent
   samples interfere and make the whole suite non-reproducible.
3. **Errors are data.** A malformed call returns a structured, deterministic
   error message rather than raising. Recovery from tool errors is one of the
   behaviours under study — SPEC-015's family depends on error text being stable
   enough to be part of the environment.

## Scope

**In scope**

- Filesystem tools: `list_dir`, `read_file`, `write_file`, `grep`, `move_file`.
- SQL tool: `run_query` over the sample's `SqlEnv`.
- Calendar tools: `list_events`, `book_slot`.
- `faulty()` — a deterministic fail-once wrapper for the error-recovery family.
- A tool registry that assembles the per-task toolset.

**Out of scope**

- Which tools a given task exposes — the task families choose (SPEC-005, 012–016).
- Harness control flow, turn caps, context policy — SPEC-007 onward.
- Scoring — SPEC-004.

## Interface contract

```python
# src/harnesslab/tools/fs.py
from inspect_ai.tool import tool, Tool
from inspect_ai.util import store_as
from harnesslab.env.models import VirtualFS


@tool
def read_file() -> Tool:
    async def execute(path: str) -> str:
        """Read a file's full contents.

        Args:
            path: Absolute path inside the workspace, e.g. /notes/todo.md

        Returns:
            The file's contents, or a structured error if it does not exist.
        """
        fs = store_as(VirtualFS)
        ...
    return execute
```

Every tool follows that shape: the docstring **is** the schema Inspect shows the
model, arguments are typed scalars, and state is reached through `store_as`.

```python
# src/harnesslab/tools/faulty.py
def faulty(inner: Tool, *, fail_on_call: int = 1, message: str | None = None) -> Tool:
    """Wrap a tool so its Nth invocation returns a deterministic error.

    Failure count is per-sample and lives in the Store, so it survives across
    turns and is recorded in the log. Deterministic by construction: no RNG, no
    wall-clock. The error-recovery family measures whether a harness retries,
    adapts, or gives up -- which is only meaningful if the failure is identical
    for every model and every harness.
    """
```

```python
# src/harnesslab/tools/registry.py
class ToolSet(StrEnum):
    FS = "fs"
    SQL = "sql"
    CALENDAR = "calendar"
    FS_FAULTY = "fs_faulty"


def tools_for(toolset: ToolSet) -> list[Tool]:
    """Assemble the toolset. Returns fresh Tool objects per sample; identical in
    schema and behaviour across every model and harness."""
```

**Invariants**

- No tool performs real I/O, network access, or clock reads.
- Every tool returns a `str`. Failures return a structured error string; they do
  not raise. Uncaught exceptions are a bug, not a task outcome.
- Error strings are deterministic: same bad input, same bytes out, with no
  paths, addresses, or timings interpolated.
- Path arguments are normalised and confined to the virtual root. `..`
  traversal, absolute escapes, and platform separators all resolve inside or
  return an error.
- `run_query` is read-only: `SELECT` and `WITH` only, one statement, executed
  against an in-memory SQLite built from the sample's `SqlEnv`.

## Design notes

**Docstrings as schema.** Inspect derives the tool schema the model sees from the
signature and docstring, so the docstring is production text, not a comment. It
is reviewed as carefully as code: an ambiguous argument description shows up as
a tool-misuse failure in the taxonomy and is easy to mistake for a model
weakness.

**Structured errors, not exceptions.** Returning `ERROR: no such file: /x/y.txt`
keeps the trajectory going and puts the recovery decision where it belongs — in
the harness. It also makes `tool_misuse` and `hallucinated_tool` cleanly
separable in SPEC-026's taxonomy.

**Read-only SQL.** Allowing writes would let a task be "solved" by mutating the
grading substrate. Final-state scoring for SQL tasks compares the *answer*, and
for filesystem tasks compares the *environment* — mixing the two would blur what
is being measured.

**`grep` returns line numbers and a bounded window.** Unbounded output is a
context-budget hazard: on an 8K-capped run one greedy `grep` can consume the
whole window and force a truncation that looks like a harness failure. Output
caps are set here, once, so they are identical everywhere.

**Rejected: a generic `bash` tool.** It is the obvious way to get breadth, and it
would wreck the experiment — the action space stops being comparable across
models, scoring stops being deterministic, and a sandbox becomes mandatory.
Narrow, typed tools are what make final-state scoring possible.

**Rejected: randomised failure for `faulty`.** Random failure would inject
variance into the exact quantity being measured. Fail-on-Nth-call is
reproducible and equally hard for the agent.

## Acceptance criteria

- **AC-1.** Every tool's Inspect-rendered schema validates: each has a
  description, and every argument has a type and a description.
- **AC-2.** A tool call cannot touch the real filesystem or network — verified
  under the I/O-forbidding fixture from SPEC-002.
- **AC-3.** Path confinement holds for `../../etc/passwd`, `/../x`, `C:\x`,
  `//server/share`, and a null byte; each returns a structured error and mutates
  nothing.
- **AC-4.** Error strings are byte-identical across repeated calls and across
  processes for the same bad input.
- **AC-5.** `run_query` rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ATTACH`,
  `PRAGMA`, and multi-statement input, leaving `SqlEnv` unchanged.
- **AC-6.** `faulty(read_file, fail_on_call=1)` fails exactly the first call and
  succeeds on the second, with the counter isolated per sample — two concurrent
  samples do not share it.
- **AC-7.** `write_file` followed by `read_file` round-trips content exactly,
  including Unicode and embedded newlines.
- **AC-8.** `grep` output is capped at the documented limit, and the cap is
  reported in the returned text rather than silently truncating.
- **AC-9.** `tools_for()` returns tools whose schemas are identical regardless of
  which harness or model requested them.

## Test plan

| Level | What it covers |
|---|---|
| unit | Schema validation for every tool (AC-1, AC-9) |
| unit | I/O-forbidding fixture (AC-2) |
| unit | Path confinement table (AC-3) |
| unit | Error determinism across subprocesses (AC-4) |
| unit | SQL read-only enforcement (AC-5) |
| unit | Round-trip and Unicode (AC-7); grep capping (AC-8) |
| integration | `faulty` isolation across two concurrent samples (AC-6) |

## Definition of done

- [ ] `make check` green
- [ ] Every AC demonstrated by a named test
- [ ] Docs updated: `docs/TASK_FAMILIES.md` tool inventory stub
- [ ] Status set to `Accepted`
