---
spec: 002
title: Deterministic procedural environment generator
status: Draft
depends_on: [000]
day: 2
---

# SPEC-002 — Deterministic procedural environment generator

## Motivation

The contamination argument for this benchmark rests on **procedural generation**:
task instances are synthesised from templates at run time, never scraped, so a
model cannot have memorised them. That argument only holds if generation is
genuinely reproducible — otherwise a published result cannot be checked, and the
claim collapses into an assertion. See `../docs/CONTAMINATION.md`.

Determinism here means something stricter than "uses a seed". It means
`generate_env(seed, spec)` produces **byte-identical** serialized state across
processes, machines, and Python versions. Anything weaker — set iteration order,
`hash()` randomisation, dict ordering, floating-point formatting — silently
breaks reproduction in ways that surface months later as unexplainable score
drift.

## Scope

**In scope**

- `StoreModel` subclasses for the three environment kinds: virtual filesystem,
  SQL, calendar.
- `generate_env(seed, spec) -> Env` and the `EnvSpec` descriptors that
  parameterise size and difficulty.
- Content fixtures: word banks, name pools, schema templates.
- Canonical serialization used for the determinism check and for scoring.

**Out of scope**

- Tools that read or mutate the environment — SPEC-003.
- Scoring against final state — SPEC-004.
- Which seeds are used for what — SPEC-023 owns the two seed regimes.

## Interface contract

```python
# src/harnesslab/env/models.py
from pydantic import Field
from inspect_ai.util import StoreModel


class FileNode(BaseModel, frozen=True):
    content: str
    # Metadata some tasks key on. Deterministic, derived from the seed --
    # never wall-clock.
    size_bytes: int
    modified_tick: int


class VirtualFS(StoreModel):
    """Sample-scoped virtual filesystem.

    Lives in Inspect's per-sample Store, so it is serialized into the .eval log
    automatically. That is what makes final-state scoring a pure function of
    data already in the log, and what lets `inspect view` show the environment a
    trajectory actually left behind. See ../docs/adr/0002.
    """

    files: dict[str, FileNode] = Field(default_factory=dict)   # POSIX paths
    cwd: str = "/"

    def canonical(self) -> str:
        """Stable JSON: sorted keys, no whitespace, LF only. The scoring and
        determinism comparisons both run over this, never over the object."""


class SqlEnv(StoreModel):
    schema_sql: str = ""
    rows: dict[str, list[dict[str, str | int | float | None]]] = Field(default_factory=dict)

    def canonical(self) -> str: ...


class CalendarEnv(StoreModel):
    events: list[Event] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)

    def canonical(self) -> str: ...
```

```python
# src/harnesslab/env/generator.py
from enum import StrEnum


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class EnvSpec(BaseModel, frozen=True):
    kind: Literal["fs", "sql", "calendar"]
    difficulty: Difficulty
    n_files: int | None = None
    depth: int | None = None
    n_tables: int | None = None
    n_rows: int | None = None
    distractor_ratio: float = 0.0   # fraction of content irrelevant to the task


def generate_env(seed: int, spec: EnvSpec) -> VirtualFS | SqlEnv | CalendarEnv:
    """Build an environment. Pure: same (seed, spec) -> byte-identical output.

    All randomness comes from a `random.Random(seed)` instance created here and
    threaded explicitly. The module-level `random` is never touched, so a
    caller's RNG state cannot leak in and ours cannot leak out.
    """
```

**Invariants**

- Purity: no wall-clock, no filesystem, no network, no environment variables, no
  process-global RNG.
- `canonical()` is stable across processes and Python versions: sorted keys,
  `separators=(",", ":")`, `ensure_ascii=True`, LF newlines, no floats where an
  int will do.
- Generation never emits a path outside the virtual root.

## Design notes

**Why the Store rather than a real temp directory or a Docker sandbox.** Inspect
serializes the per-sample Store into the `.eval` log for free, which means the
final environment state is (a) available to the scorer as data, (b) visible in
`inspect view`, and (c) reproducible from the log alone. A real filesystem gives
none of those and costs container startup per sample. `SandboxEnvironment` is for
untrusted *code execution*, which this suite deliberately never does. See
`../docs/adr/0002`.

**`modified_tick`, not `mtime`.** A timestamp would make output depend on when it
ran. A monotonic tick derived from generation order gives tasks something to sort
and filter on while staying pure.

**Distractors are generated, not sampled from a fixed list.** The
`distractor_ratio` produces plausible irrelevant content so difficulty comes from
discrimination, not from volume alone.

**Rejected: seeding the global `random` module.** It works until something else
in the process — pytest-randomly, a library import — touches it. Threading an
explicit `Random` instance is marginally more verbose and cannot be undermined.

**Rejected: `hash()` for any derived value.** Python randomises string hashing
per process unless `PYTHONHASHSEED` is fixed, and relying on an environment
variable for correctness is a trap.

## Acceptance criteria

- **AC-1.** For every `(seed, spec)` in a fixed matrix, `generate_env` called
  twice **in separate subprocesses** yields identical SHA-256 of `canonical()`.
- **AC-2.** The same holds with `PYTHONHASHSEED` set to different values across
  the two subprocesses — proving no reliance on hash ordering.
- **AC-3.** Different seeds produce different environments: over 100 seeds at
  fixed spec, `canonical()` digests are pairwise distinct.
- **AC-4.** Difficulty is monotone in the structural measure it claims —
  `EASY < MEDIUM < HARD` in file count and directory depth for `fs`, and in join
  depth for `sql`.
- **AC-5.** `generate_env` performs no I/O. Verified with a fixture that patches
  `open`, `Path.open`, `socket.socket`, and `time.time` to raise.
- **AC-6.** No generated path escapes the virtual root, including via `..`
  segments, absolute prefixes, or platform separators.
- **AC-7.** `canonical()` output is byte-identical on Windows and Linux for the
  same input — no `os.sep` or `os.linesep` leakage. Verified in CI on both.

## Test plan

| Level | What it covers |
|---|---|
| unit | Subprocess determinism matrix (AC-1, AC-2) |
| unit | Seed dispersion over 100 seeds (AC-3) |
| unit | Difficulty monotonicity (AC-4) |
| unit | I/O-forbidding fixture (AC-5) |
| unit | Path escape attempts (AC-6) |
| golden | Committed digests for a small fixed matrix — catches accidental content drift |
| integration | CI matrix runs the suite on `windows-latest` and `ubuntu-latest` (AC-7) |

Note the golden digests are a deliberate tripwire: any change to the fixtures or
generation logic breaks them, which forces a conscious decision about whether
previously published results are still comparable.

## Definition of done

- [ ] `make check` green on both Windows and Linux
- [ ] Every AC demonstrated by a named test
- [ ] Docs updated: `docs/CONTAMINATION.md`, `docs/adr/0002`
- [ ] Status set to `Accepted`
