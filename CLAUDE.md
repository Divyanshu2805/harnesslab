# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## The repository is pre-implementation

`src/harnesslab/` is **empty**. What exists is a spec system (`specs/`), the
methodology (`docs/`), and the scaffold. No implementation code is written until
its spec is individually approved — see "Spec-driven workflow" below.

This is a research-engineering project whose output is a *claim* about measured
effects. Most of the constraints below exist because they determine whether that
claim means what it says, not because of style preference.

## Commands

```bash
uv sync --extra dev          # install
make check                   # the per-spec gate: scaffold + lint + types + tests
make scaffold                # spec dependency/ordering/link checks (instant)
make fmt                     # ruff format + autofix
```

```bash
uv run pytest tests/unit/test_generator.py::test_determinism    # single test
uv run pytest -m "not network and not gpu"                      # what `make test` runs
uv run pytest -m network     # hits live providers — SPENDS QUOTA
uv run pytest -m gpu         # needs local Ollama with Lane A models
```

```bash
uv run harnesslab run --task fs.reorganise --model ollama/qwen2.5:7b
uv run harnesslab budget --plan plans/laneA.json    # forecast before spending
make providers               # re-verify live quotas, regenerate docs/PROVIDERS.md
```

**`make check` must never make a network call.** This is a budget property, not
hygiene: free-tier quota is the experiment's scarcest resource, and a suite that
quietly spent tokens per run would consume what the experiment needs. It is also
what lets CI pass on fork PRs, which cannot read secrets. Anything touching a
provider gets the `network` marker; anything needing the GPU gets `gpu`.

`make scaffold` (`scripts/verify_scaffold.py`) enforces that spec dependencies
resolve, that no dependency is scheduled *after* its dependant, that required docs
exist, and that no internal links dangle. It runs first because it catches
planning errors invisible to the type checker.

## Spec-driven workflow

**One spec is implemented, reviewed, and merged at a time.**

- `specs/ROADMAP.md` is the execution order. **Spec IDs are allocation order, not
  execution order** — 028–031 were added later and run mid-project. Read the
  roadmap, not the filenames.
- Specs 000–006 are written in full (interface contracts, acceptance criteria).
  007–031 are **stubs**: scope and acceptance criteria only. A stub is sharpened
  into a full spec when its dependencies land, so the contract is written from
  knowledge rather than guesswork. **Do not write an interface contract for a
  stub before its dependencies exist** — a stale spec is worse than an absent one.
- Definition of done: `make check` green, every numbered AC demonstrated *by a
  test*, docs updated in the same change, status set to `Accepted`.

Design decisions live in `docs/adr/` (11 records), each naming the alternatives
rejected. Check there before changing something that looks arbitrary.

## Architecture

### Two lanes, and they contend for nothing

| | Lane A | Lane B |
|---|---|---|
| Runtime | Ollama on an RTX 4060, 8 GB | Groq · Gemini · Cerebras · OpenRouter |
| Bound by | GPU throughput | Daily token/request quota |
| Carries | Headline ablation, full harness axis, compaction ablation | Cost/Pareto claim |

One is GPU-bound, the other API-quota-bound in CI, so they run **concurrently**.
The pooled primary grid is 8 models × 3 harnesses × 20 tasks.

### The cost architecture is structural

Evaluation runs in scheduled CI and on local hardware; the leaderboard is
prebuilt static files on GitHub Pages. **A visitor cannot trigger a model call
because no code path exists** — not because a rate limiter declines. Do not
introduce a backend, a serverless function, or any request-path provider access.
(`docs/adr/0006`)

### What Inspect AI supplies, and what is deliberately declined

Built on Inspect (UK AI Security Institute). Three things are used and three
declined; the declines are load-bearing:

- **`StoreModel`, not `SandboxEnvironment`.** Environments (virtual FS, SQL,
  calendar) are Pydantic models in Inspect's per-sample Store. Inspect serializes
  them into the `.eval` log, so final-state scoring is a pure function of data
  already in the log, and **a published log can be re-scored without rerunning
  any model**. No Docker. (`adr/0002`)
- **Native providers, no LiteLLM.** `groq/`, `google/`, `mistral/`, `ollama/`,
  `openrouter/` are native; Cerebras rides `openai-api/cerebras/<model>`. Two
  token-accounting paths would corrupt the cost model. (`adr/0001`)
- **`samples_df()` is the ingest path.** It already yields per-sample tokens,
  timing, scores, errors. Do not build a parallel telemetry layer.
- **No `model_graded_qa()`.** See below.

### Invariants that keep the experiment valid

Breaking any of these silently invalidates results rather than causing an error:

- **A harness never branches on model identity**, and **a scorer never inspects
  the harness.** The measuring instrument must be indifferent to the variable
  being varied.
- **Every model call is booked in the ledger** — including retries, failures, and
  one-off validation runs. An unrecorded call is a quota leak *and* a
  reproducibility gap.
- **One context policy across every pooled cell** (8K cap). Mixing capped and
  uncapped runs confounds the model axis with context policy.
- **Analyses never pool across `seed_regime` or `context_policy`.** The code
  raises rather than silently averaging.

## Constraints that will bite

**Token budget is the binding constraint, and it is quadratic.** The limit is
usually tokens/day, not requests/day (Groq's 70B: 1,000 RPD but **100K TPD** ≈ 6
trajectories). A ReAct trajectory resends its history every turn, so input grows
with the *square* of turn count — 8 turns ≈ 15K tokens, not 2K. Sizing anything
linearly is how the original plan came out an order of magnitude wrong.
`docs/TOKEN_BUDGET.md` has the arithmetic.

**The 8,192-token Cerebras context cap drives the whole design.** It forces the
shared context policy, which in turn creates the project's sharpest risk: the
mechanism by which `plan_execute` and `react_reflect` help *is carrying more
context*, so the cap may erase the effect being measured. Block A3 quantifies
that. Read `docs/adr/0008` before touching context handling.

**No LLM judge anywhere** — not in scoring, not in failure classification. Judge
models favour verbose, confident output, and that preference is *aligned with the
independent variable*. This is why tasks must be deterministically scorable, and
why the suite excludes open-ended generation. (`adr/0004`)

**Ollama models are pinned by `sha256:` digest, never tag.** Tags move; a result
that cannot be reproduced in six months is not a result. (`adr/0011`)

**`docs/PROVIDERS.md` is generated, not hand-edited** — quotas carry fetch dates
and source URLs because they expire. Free tiers change monthly.

**Line endings are pinned to LF via `.gitattributes`** because `generate_env()`
must produce byte-identical output on Windows and Linux (SPEC-002 AC-7).

## Start here

`docs/EXPERIMENT_DESIGN.md` for the design and why it is shaped this way;
`specs/ROADMAP.md` for what to build next; `docs/README.md` indexes the rest.
