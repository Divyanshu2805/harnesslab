# ADR 0008 — One context policy across the pooled grid, plus a crossed compaction ablation

**Status:** ⚠️ **PREMISE INVALIDATED — awaiting decision** · **Date:** 2026-08-09

> **Day 1 probe finding.** This ADR's central premise was that Cerebras' free
> tier caps context at 8,192 tokens and that Lane B is therefore *forced* into
> compaction. **Cerebras' free tier is unavailable** — inference returns
> HTTP 402, "Payment required to access this resource" — and the model has been
> withdrawn from the pooled grid.
>
> With it gone, the tightest context ceiling in the grid is 32,768. **Nothing
> now forces an 8K shared policy.**
>
> The new binding constraint is **Groq's 6,000 TPM**, confirmed empirically by a
> `429 ... on tokens per minute (TPM): Limit 6000` at ~7K tokens. That is
> *tighter* than the ceiling it replaces, but it is a **rate limit rather than a
> per-request cap** — it throttles throughput rather than truncating history, so
> it does not motivate the same design in the same way.
>
> **The decision below is not yet re-made.** Three options, in
> `specs/SPEC-001-provider-registry.md` § Day 1 outcome:
> keep an 8K cap as a deliberate comparability choice rather than a forced one;
> raise the cap, since nothing compels 8K and a higher ceiling is less likely to
> suppress the reflective harnesses; or restore Cerebras if a free tier
> reappears. **No sweep may run until this is resolved** — the choice determines
> whether the headline is a lower bound.

---

> **This is the most consequential decision in the project, and the one most
> likely to be wrong in a way that produces a confident false conclusion.**

## Context

Cerebras' free tier caps context at **8,192 tokens**. Groq's free TPM (6K–12K)
throttles below a long trajectory's per-call footprint. Lane A on a 4060 has
neither constraint.

If the pooled grid mixed capped and uncapped runs, **the model axis would be
confounded with context policy**. Lane B models could score lower because their
histories were truncated rather than because they are less capable, and the
headline comparison would be invalid.

The obvious fix — cap everything — creates a second problem that is easy to miss.

## The problem the obvious fix creates

**The mechanism by which `plan_execute` and `react_reflect` are supposed to help
is carrying more context** — more turns, more accumulated observations, room to
self-critique.

Cap everything at 8K and the control may **erase precisely the advantage being
measured**. The experiment would then report "harness barely matters" as an
artefact of the experimenter's own design choice, with a clean confound-free grid
and a completely wrong conclusion.

An earlier revision of the plan had exactly this hole: the compaction ablation
covered only the three *common* harnesses, so **the two harnesses most likely to
need long context were never run uncapped.**

## Decision

**Two parts, and the second is not optional.**

**1. Every cell in the pooled primary grid runs an identical 8K-capped context
policy**, Lane A included, even though Lane A does not need it. This removes the
confound.

**2. Block A3 crosses the compaction ablation on the full five-harness axis** —
2 models × **all 5 harnesses** × 20 tasks × 3 seeds, uncapped, paired
cell-for-cell against the capped runs (same task, seed, harness, model; differing
only in policy).

A3 trades a *model* for two *harnesses* deliberately: the effect of interest is a
**harness × policy interaction**, not a model × policy one. The 3B model is
dropped as least likely to exploit long context or self-critique coherently.

**3. Pre-declared reporting rule:**

> If A3 shows the cap materially suppresses `plan_execute` or `react_reflect`,
> the pooled estimate is reported as a **directional lower bound on the harness
> effect**, with the suppression quantified — **in the abstract, not a footnote**.

## Consequences

**Good.** The confound is removed *and* its cost is measured. The risk becomes a
**reported number** rather than an unexamined assumption.

**Good.** "Does history compaction cost accuracy, and does it differ by harness?"
becomes a second finding, and a practically useful one — anyone running agents
against a context-capped free tier needs that answer.

**Good.** A null result is now interpretable. A null under a suppressing cap
means something different from a null without one, and a reader can tell which
they are looking at.

**Cost.** +600 uncapped Lane A trajectories, and uncapped trajectories cost ~1.5×
the wall time of capped ones (more retained context, more prefill per turn). Lane
A grows from ~40 to **~52 GPU-hours**, from 5–6 nights to ~7. A3 runs **second**,
after A1, so the answer arrives before the paper is written; the cut ladder
reduces its seeds first if time runs short.

**Cost.** `context_exhausted` becomes a first-class outcome that must be recorded
and kept distinct from `turn_cap_exhausted` and from ordinary task failure
([SPEC-009 AC-6](../../specs/SPEC-009-harness-reflect-compaction.md)).
Misattributing a cap effect to model reasoning is exactly the error this ADR
exists to prevent.

## Alternatives rejected

**Let each lane use whatever policy it can afford.** The original approach.
Confounds the model axis with context policy, invalidating the headline.

**Drop Cerebras and raise the shared cap.** Buys a larger ceiling at the cost of
a model on the axis and of representativeness — an 8K cap is a real constraint
real people hit, and pretending otherwise makes the result less useful.

**Cap everything and note the limitation in prose.** Cheapest option. Rejected
because "the cap may have suppressed the effect" is unfalsifiable as prose, and
the reviewer's obvious next question — *by how much?* — would have no answer.

**Run A3 uncapped on all three models but only the common harnesses.** The
earlier revision. More models, but blind on exactly the two harnesses whose
mechanism is context retention.
