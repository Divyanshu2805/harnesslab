# ADR 0002 — Use Inspect's typed `Store`, not a custom `SandboxEnvironment`

**Status:** Accepted · **Date:** 2026-08-09

## Context

Tasks need an environment the agent manipulates: a filesystem, a database, a
calendar. The original plan proposed a "local in-process virtual FS + SQLite"
built alongside Inspect, with Docker-per-task explicitly rejected for overhead.

Inspect offers two mechanisms. `SandboxEnvironment` (docker, k8s, local, …) is
built for **executing untrusted code**. `Store` is a **sample-scoped scratchpad**,
and `StoreModel` gives it a Pydantic type.

This suite never executes untrusted code. Its tools are narrow and typed by
design — see ADR 0004, since that narrowness is what makes deterministic scoring
possible at all.

## Decision

Environments are `StoreModel` subclasses, reached from tools via
`store_as(VirtualFS)`. **No `SandboxEnvironment`, no Docker, no real filesystem.**

## Consequences

Three properties fall out, and each removes work that would otherwise need
building:

1. **Final-state scoring is a pure function of data already in the log.** Inspect
   serializes the Store into the `.eval` log automatically, so the scorer reads
   the environment the agent left behind without any bespoke capture step.
2. **A published log can be re-scored without rerunning any model.** If a scorer
   bug is found after the sweep, it is fixed and the logs are re-scored — no
   quota spent. On free tiers that is close to decisive.
3. **`inspect view` shows the final environment for free**, which makes failure
   analysis (SPEC-026) tractable by hand.

Plus: no container startup per sample, and sample isolation by construction —
concurrent samples cannot interfere, because there is no shared substrate.

**Cost.** Environments must be expressible as serializable Pydantic models. No
real subprocesses, no genuine file permissions, no network simulation. Acceptable,
and a consequence of the same constraint that ADR 0004 accepts.

## Alternatives rejected

**Docker sandbox per task.** Realistic, and the standard choice for agent
benchmarks. Rejected on cost — container startup per sample across ~2,700
trajectories is significant, especially against a 4060 already saturated by
inference — and because it would give up all three properties above.

**A hand-rolled in-process VFS beside Inspect** (the original plan). Would have
worked, and would have meant writing serialization, log capture, and viewer
integration that `StoreModel` provides. Strictly more code for strictly less.

**`local` sandbox.** Real filesystem access with no isolation. Concurrent samples
would interfere, and determinism would depend on cleanup being perfect.
