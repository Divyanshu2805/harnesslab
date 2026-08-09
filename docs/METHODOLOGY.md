# Methodology

What counts as correct, how cost is computed, how seeds work, and which lane
supports which claim. This is the document to cite when a number is questioned.

---

## 1. What counts as correct

**Scoring is deterministic. There is no LLM judge anywhere in this project** —
not in scoring, and not in the failure taxonomy.

A model-graded scorer would reintroduce precisely the bias the experiment exists
to measure around. Judge models have known preferences over response style, so
any harness producing more verbose or more confident output would score higher
for reasons unrelated to task success. Since the *only* thing varying across the
harness axis is the scaffold, the measuring instrument must be indifferent to it.

Four scorers, all pure functions of `(final state, target)`:

| Scorer | Decides correctness by |
|---|---|
| `final_state` | Byte comparison of the canonical environment against a target derived from the same seed |
| `exact_match` | Normalised comparison of a submitted answer |
| `refusal` | Three conjoint conditions — see §2 |
| `partial_credit` | Fraction of independently-checkable sub-goals; **diagnostic only** |

**Normalisation is narrow and written down**: strip surrounding whitespace,
collapse internal whitespace runs, casefold, strip one trailing period. Nothing
else. No synonym matching, no numeric tolerance, no fuzzy distance. Every extra
rule is a place where a scaffold that formats differently could gain an edge.

**The headline metric is binary task success.** Partial credit is reported
alongside but never substituted: "one third of a filesystem task" and "one third
of a SQL task" are not the same quantity, so partial credit does not aggregate
across families.

**The cost of this commitment** is that tasks must be constructed so correctness
is decidable from state — no open-ended writing. That constrains what this
benchmark can cover, and the constraint is stated in `LIMITATIONS.md` rather than
elided.

---

## 2. Refusal is scored three-way, not two-way

Benchmarks report success on solvable tasks and say nothing about whether an
agent knows when to stop. The interesting failure is an agent that **neither
solves nor declines**.

`refusal()` returns 1.0 only when **all three** hold:

1. the agent **submitted** rather than exhausting its turn budget,
2. the submission is classified as a refusal by a deterministic rule, and
3. the environment is **unmodified** — nothing fabricated was left behind.

Without condition 1, a turn-cap timeout would be indistinguishable from an honest
"this cannot be done". Without condition 3, an agent could fabricate a plausible
artifact, declare the task impossible, and score as if it had behaved well.

The classifier is a deterministic rule set, not a model. It will have false
negatives on unusual phrasings. That cost is accepted, and its **error rate is
measured against ≥50 hand-labelled submissions and reported as a number**
([SPEC-016 AC-6](../specs/SPEC-016-family-refusal.md)) rather than left unknown.

**Refusal accuracy is reported as its own metric and never averaged into overall
task success.** They measure different things.

---

## 3. How cost is computed

Execution is free; the economics are real. Token counts are actual, prices are
the vendor's own published paid rates, and the product is a **notional cost** —
what this work would cost at scale.

Two cost bases, kept separate:

- **Lane B** — published per-token pricing.
- **Lane A** — GPU-hour rental equivalent (spot rate ÷ measured
  trajectories-per-hour), with electricity reported separately as a lower bound.

**The two bases are not equivalent, and the charts say so on the chart itself.**
API prices embed provider margin and model-training amortisation; GPU rental
embeds hardware amortisation but not training. Cross-lane comparison is
*indicative, not equivalent* — it supports order-of-magnitude statements, not
precise ratios.

**Failed and retried calls are counted.** A retry spends real tokens, and
excluding them would flatter exactly the harnesses that retry most — which is a
dimension under study.

Prices are versioned with fetch dates, and cost is computed from the table **in
force on the run's date**, not the table current at ingest. Full detail in
[COST_MODEL.md](COST_MODEL.md).

---

## 4. How seeds work

Seeds do two unrelated jobs, so there are two regimes, and analyses never pool
across them:

| Regime | Behaviour | Purpose |
|---|---|---|
| `primary` | Fixed set of 5, committed, **immutable once the sweep starts** | Replication unit for the bootstrap; produces the paper |
| `rotating` | Fresh per scheduled run, derived deterministically from the run date | Contamination defence for the live public leaderboard |

**The primary experiment's contamination resistance comes from the generator
being procedural — not from rotation.** Tasks are synthesised from templates and
never scraped, so no instance existed to be memorised. Rotation defends the
*ongoing leaderboard* against *future* contamination, which is a different threat
on a different timescale. Conflating the two is the mistake this separation
exists to prevent. See [CONTAMINATION.md](CONTAMINATION.md).

---

## 5. Lane attribution

**Every published claim names the lane that supports it.** The two lanes answer
different questions and have different statistical weight.

| Claim | Lane | Why |
|---|---|---|
| Harness effect vs model effect (headline) | Pooled A1 + B | 8 models × 3 harnesses, identical context policy |
| Full 5-harness comparison | A only | Lane B quota cannot afford the extended axis |
| Does compaction cost accuracy | A only (block A3) | Lane B is *forced* to compact; only Lane A can run the control |
| Accuracy vs cost / Pareto | Both, bases distinguished | See §3 |
| "Works on hardware a student owns" | A only | That is the question Lane A asks |
| "Works on a free API key" | B only | That is the question Lane B asks |

Numbers from quota-starved providers (Groq 70B at ~6 trajectories/day,
OpenRouter at ~6) always carry their N.

---

## 6. Failure classification is manual

The taxonomy is coded **by hand, never by a model**. Using an LLM to classify
failures would reintroduce judge bias at exactly the point where the qualitative
story is told, and the whole argument for deterministic scoring would collapse.

- 150 failed trajectories, stratified by model × harness.
- Coding sheets are pre-populated with metadata so the human makes only the
  category judgment.
- A second pass over 50 after a ≥48 h gap reports Cohen's κ.

With a single coder this is **intra-rater** agreement (test–retest), which is the
honest ceiling; inter-rater κ requires a second person and is strictly better if
one is available. Either way the limitation is stated, not glossed.

---

## 7. What is fixed before data exists

Because most of these choices determine what the data can mean:

- The estimator and its clustering unit — [EXPERIMENT_DESIGN.md §5](EXPERIMENT_DESIGN.md)
- The context policy across the pooled grid — §4 of the same
- The three pre-declared outcomes, including the null — [PREREGISTRATION.md](PREREGISTRATION.md)
- The stopping rule and the cut ladder
- The core-20 suite, selected on **baseline data only**

That last point deserves emphasis: tasks are selected for being discriminating
using pre-sweep baselines, **never** using primary-sweep results. Selecting tasks
on the outcome they will be used to measure is the purest form of the bias this
project is built to avoid, and
[SPEC-017 AC-4](../specs/SPEC-017-core-suite-selection.md) enforces the ordering
by commit timestamp.
