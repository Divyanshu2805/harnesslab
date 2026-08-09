# HarnessLab

**Does the scaffolding around a model matter more than the model — measured on
hardware and APIs people can actually afford?**

A controlled two-dimensional ablation over **models × agent harnesses** on a
fixed, procedurally generated task suite. Hold the model fixed and vary the
scaffold; hold the scaffold fixed and vary the model. The popular claim that
*"the harness matters as much as the weights"* asserts a comparison between those
two effects without measuring it. This measures it.

A leaderboard is published as a by-product, not as the contribution.

> **Status: pre-implementation.** The design, specs, and methodology are complete
> and committed. No results exist yet. Every number below is a placeholder until
> the sweeps run — see [`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md) for
> what was committed to before any data existed.

## Progress

<!-- BEGIN GENERATED: progress -->

`····························`  **0 / 32 specs accepted**

Draft 32

**Next:** SPEC-000 — Repo scaffold, uv, tooling, CI skeleton (day 1, Draft)

9 documents · 11 ADRs · 0 implementation files

<!-- END GENERATED: progress -->

<sub>Regenerated from spec frontmatter by the pre-commit hook — never edit by hand.</sub>

---

## The finding

> _Filled after Day 32. Not before._

Ran a controlled ablation over **[N]** models × **[M]** agent harnesses on a
**[K]**-task suite (**[T]** trajectories), showing scaffold choice shifted task
success by **[X]** percentage points versus **[Y]** for model choice
(95% CI **[…]**).

---

## Two lanes

"Affordable compute" has two populations, and each gets a lane. Neither is a
compromise for the other.

| | **Lane A — consumer hardware** | **Lane B — free-tier APIs** |
|---|---|---|
| Question | *What works on a GPU you own?* | *What works on a free API key?* |
| Runtime | Ollama on an RTX 4060, 8 GB | Groq · Gemini · Cerebras · OpenRouter |
| Models | 3, spanning 3B → 12B at 4-bit | 5 hosted |
| Seeds | 5 | 2 |

They share a 20-task core suite and three harnesses, so the pooled primary grid
is **8 models × 3 harnesses × 20 tasks**.

---

## What makes the numbers mean something

**No LLM judge — anywhere.** Scoring is deterministic: final-state comparison and
exact match. A judge model would favour verbose, confident output, and that
preference is *aligned with the independent variable* — reflective harnesses
produce more text almost by construction. Failure classification is manual for
the same reason. ([ADR 0004](docs/adr/0004-no-llm-judge.md))

**Contamination-resistant by construction.** Tasks are synthesised from templates
at run time, never scraped. No instance existed to be memorised. The two seed
regimes — fixed for the paper, rotating for the live board — do different jobs and
are never pooled. ([CONTAMINATION.md](docs/CONTAMINATION.md))

**Pre-registered.** Hypothesis, estimator, null criteria, and stopping rule
committed to git before any sweep data existed. The commit hash is cited in the
paper. ([PREREGISTRATION.md](docs/PREREGISTRATION.md))

**One context policy across the pooled grid** — because Cerebras' free tier caps
context at 8,192 tokens, and mixing capped with uncapped runs would confound the
model axis with context policy. That control creates its own risk (the reflective
harnesses' whole mechanism is carrying more context), so a crossed ablation
measures how much the cap suppresses them, and the headline is reported as a
lower bound if it does. ([ADR 0008](docs/adr/0008-shared-context-policy.md))

**Notional cost, honestly.** Free execution, real economics: actual token counts
× the vendor's published paid rates. Local inference is priced by GPU-hour rental
equivalent. **The two bases are not equivalent**, and the charts say so on the
chart. ([COST_MODEL.md](docs/COST_MODEL.md))

**$0 by construction.** Evaluation runs in scheduled CI and on local hardware;
the leaderboard is prebuilt static files. A visitor cannot trigger a model call
because no code path exists — not because a rate limiter declines.
([ADR 0006](docs/adr/0006-static-serving-lane.md))

---

## Quick start

```bash
uv sync --extra dev
```

```bash
make check
```

`make check` runs lint, types, and tests with **zero network calls**. Tests
needing a provider carry the `network` marker; those needing the GPU carry `gpu`.
Neither runs by default — the project's free quota is the experiment's scarcest
resource.

Run one task against one model:

```bash
uv run harnesslab run --task fs.reorganise --model ollama/qwen2.5:7b
```

Forecast a sweep before spending anything on it:

```bash
uv run harnesslab budget --plan plans/laneA.json
```

Copy `.env.example` to `.env` for provider keys. Every key is a free tier; see
[`docs/PROVIDERS.md`](docs/PROVIDERS.md) for current quotas with fetch dates.

---

## How this repository is organised

Built **spec by spec** — one implemented, reviewed, and merged at a time.

| Path | What is there |
|---|---|
| [`specs/`](specs/) | 32 specs. [`ROADMAP.md`](specs/ROADMAP.md) is the execution order — read it first |
| [`docs/`](docs/) | What was decided and why. [Index](docs/README.md) |
| [`docs/adr/`](docs/adr/) | Eleven decision records, each naming the alternatives rejected |
| `src/harnesslab/` | Implementation (pending — no code until Spec 000 is approved) |
| `site/` · `paper/` | The static leaderboard and the LaTeX paper |

Start with [`docs/EXPERIMENT_DESIGN.md`](docs/EXPERIMENT_DESIGN.md) for the
design, or [`docs/TOKEN_BUDGET.md`](docs/TOKEN_BUDGET.md) for the arithmetic that
sizes it.

---

## Reproducing a result

Every result row records `git_sha`, `seed`, `seed_regime`, `model_digest`,
`quantization`, `context_policy`, and `block_id`. Given a row you can regenerate
the exact task instance and re-run the exact configuration.

Ollama models are pinned by **digest, not tag** — tags move, and
`ollama/qwen2.5:7b` six months from now will not be the weights that produced
these numbers. ([ADR 0011](docs/adr/0011-pin-model-digests.md))

Because the environment is serialized into each `.eval` log, **a published log
can be re-scored without rerunning any model**.

---

## Prior work

This builds on, and does not claim to have discovered, the argument that cost is
systematically omitted from agent leaderboards — see **HAL** and **AstaBench**.
It tests a stronger version of that claim. Related evaluation work includes
τ-bench, AgentBench, GAIA, and WebArena; the harnesses implement patterns from
the ReAct, Reflexion, and plan-and-solve literature.

Full positioning in `docs/RELATED_WORK.md` (written Days 20–21).

---

## What this cannot answer

- **Only deterministically scorable tasks** — no open-ended generation. That is
  the price of refusing a judge model.
- **Small local models.** Lane A tops out near 12B at 4-bit on 8 GB; nothing here
  speaks to scaffold effects at frontier scale.
- **Low N on quota-starved providers.** Groq's 70B (100K tokens/day) and
  OpenRouter (50 requests/day) appear at low N, disclosed wherever reported.
- **Five harnesses, one implementation each.** A negative result about
  `react_reflect` is about *this* implementation, not about reflection as an idea.
- **Twenty task templates** is not many clusters for a bootstrap. Interval widths
  will show it, which is why the minimum detectable effect is reported regardless
  of outcome.

---

## Licence

Code **Apache-2.0** ([LICENSE](LICENSE)). Task suite, results, and trajectories
**CC-BY-4.0** ([LICENSE-DATA](LICENSE-DATA)). Rights in model-generated text are
governed by the terms of the provider that generated it.

Built on [Inspect AI](https://inspect.aisi.org.uk/) (UK AI Security Institute).
