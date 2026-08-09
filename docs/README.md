# Documentation index

Specs describe **what to build** (`../specs/`). These documents describe **what
was decided and why**.

<!-- BEGIN GENERATED: doc-counts -->

32 specs · 9 documents · 11 ADRs · synced at `(no commits yet)`

<!-- END GENERATED: doc-counts -->


## Written in full, before implementation

The criterion is simple: **if a decision constrains the experimental design, it
is written before the design is built.** A choice made after seeing data is not
the same choice.

| Document | What it settles |
|---|---|
| [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md) | The two lanes, the pooled grid, the context-policy control and the risk it creates, the estimator, execution order and the cut ladder, the three pre-declared outcomes |
| [PREREGISTRATION.md](PREREGISTRATION.md) | Hypothesis, estimand, primary and secondary analyses, null criteria, stopping rule. **Committed before any sweep data exists; the commit hash is cited in the paper** |
| [METHODOLOGY.md](METHODOLOGY.md) | What counts as correct, how cost is computed, how seeds work, which lane supports which claim |
| [ARCHITECTURE.md](ARCHITECTURE.md) | The two-lane system design, what Inspect supplies and what is declined, the module map, the offline guarantee |
| [TOKEN_BUDGET.md](TOKEN_BUDGET.md) | The arithmetic that sizes the whole experiment, provider capacity, GPU-hours per model, named reservations, admission control |
| [COST_MODEL.md](COST_MODEL.md) | Notional cost; the two non-equivalent cost bases; cost per solved task |
| [CONTAMINATION.md](CONTAMINATION.md) | Why the suite resists memorisation, the two seed regimes, and what is **not** defended |
| [PROVIDERS.md](PROVIDERS.md) | Verified free-tier limits with fetch dates and sources — generated, never hand-edited |
| [PUBLICATION.md](PUBLICATION.md) | The publication workstream, tracked from Day 15 |

## Written just in time

Deferred deliberately. Writing these before their subject matter exists produces
documents that are wrong in ways nobody notices, and **a stale document is worse
than an absent one**.

`TASK_FAMILIES.md` · `HARNESSES.md` · `SCORING.md` · `RESULTS_SCHEMA.md` ·
`STATISTICS.md` · `FAILURE_TAXONOMY.md` · `LIMITATIONS.md` · `GLOSSARY.md`

`RELATED_WORK.md` is the exception among these — it is **scheduled**, with two
dedicated days (20–21), because positioning against HAL, AstaBench, τ-bench,
AgentBench, GAIA, WebArena and the ReAct / Reflexion / plan-and-solve papers is
real reading rather than a paragraph written at the end.

## Decision records

[`adr/`](adr/) holds one record per design decision, each naming the alternatives
rejected and why. A surprising choice should be traceable to a document that
says whether it was deliberate.

| ADR | Decision |
|---|---|
| [0001](adr/0001-drop-litellm.md) | Drop LiteLLM; use Inspect's native providers |
| [0002](adr/0002-store-not-sandbox.md) | Use Inspect's typed `Store`, not a custom `SandboxEnvironment` |
| [0003](adr/0003-token-budget-first.md) | Token budget as a Week-1 component with admission control |
| [0004](adr/0004-no-llm-judge.md) | Deterministic scoring; no LLM judge anywhere |
| [0005](adr/0005-two-lanes.md) | Two first-class lanes, not one lane and a compromise |
| [0006](adr/0006-static-serving-lane.md) | Static serving lane; the expensive path is unreachable |
| [0007](adr/0007-bootstrap-not-anova.md) | Cluster bootstrap on task template, not two-way ANOVA |
| [0008](adr/0008-shared-context-policy.md) | One context policy across the pooled grid, plus a crossed compaction ablation |
| [0009](adr/0009-two-seed-regimes.md) | Two seed regimes: fixed primary, rotating public |
| [0010](adr/0010-solvability-gate.md) | Every task validated solvable before any sweep |
| [0011](adr/0011-pin-model-digests.md) | Pin Ollama digests, never tags |
