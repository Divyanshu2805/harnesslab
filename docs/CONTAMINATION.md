# Contamination control

A benchmark whose tasks are on the public internet measures memorisation as much
as capability. This document states what protects this suite, and — more
importantly — **what does not**, because the distinction is exactly what a
reviewer will probe.

---

## 1. The argument rests on procedural generation

**Tasks are synthesised from templates at run time. They are never scraped, never
hand-written as fixed instances, and no instance exists to be memorised.**

A task definition in this repository contains no content. It contains a
*generator call*: `generate_env(seed, spec)` builds the filesystem, the database,
or the calendar, and a pure function derives the target state from the same seed.
Two seeds produce genuinely different instances — different filenames, different
contents, different distractors, different answers.

This is the load-bearing claim, and it is enforced mechanically:
[SPEC-005 AC-8](../specs/SPEC-005-task-family-filesystem.md) fails the build if
any task definition contains generated content.

---

## 2. Seed rotation is **not** what makes the primary experiment sound

This is the point most easily conflated, and stating it plainly is worth more
than an extra defence.

Seeds do **two unrelated jobs**:

| Job | Requirement | Regime |
|---|---|---|
| Replication unit for the bootstrap | Seeds must be **fixed** — rotating them makes results impossible to pool across runs, and makes the published interval unreproducible | `primary` |
| Contamination defence for the live leaderboard | Seeds must **rotate** — so a model trained on scraped leaderboard content gains nothing | `rotating` |

If you conflate them, one job breaks. So there are two regimes, both recorded on
every result row, and the analysis **refuses to pool across them** rather than
silently averaging ([SPEC-024 AC-5](../specs/SPEC-024-bootstrap-core.md)).

> **The primary experiment's contamination resistance comes from the generator
> being procedural, not from rotation.** Rotation defends the *ongoing public
> leaderboard* against *future* contamination — a different threat, on a
> different timescale.

---

## 3. The two regimes

### `primary` — fixed, versioned, immutable

- `data/seeds/primary-v1.json`, five seeds, committed.
- **Immutable once the primary sweep starts.** Enforced by
  [SPEC-023 AC-2](../specs/SPEC-023-seed-regimes.md): the test fails if the file
  changes while any `seed_regime='primary'` row exists.
- Produces the paper. Enables exact reproduction and clean pooling.

### `rotating` — fresh per scheduled run

- Derived deterministically from the run date, so a published leaderboard entry
  remains reproducible even though the seeds differ between runs.
- Never collides with the primary set.
- Feeds the public leaderboard only.

**The public leaderboard shows only rotating results; the paper uses only
primary. Neither borrows from the other.**

---

## 4. Threats this does and does not address

| Threat | Addressed? | How |
|---|---|---|
| Task instances in pretraining data | **Yes** | No instance existed before generation |
| Task *templates* leaking into future training | Partly | Templates are public in this repo. A model could learn the *shape*. Rotation means it cannot learn the *answers* |
| Leaderboard results scraped into training | **Yes**, for the live board | Rotating seeds; a memorised answer is wrong on a fresh instance |
| Provider-side caching inflating results | **Yes** | Fresh instances per seed defeat prompt caching across cells |
| A model trained specifically on this generator | **No** | Nothing defends against this. It is disclosed in `LIMITATIONS.md` |
| Solution leakage through the reference solutions | Partly | Reference solutions are committed and public. They describe *how* to solve a template, not the answer to any instance |

The honest reading of row 2 and row 6: publishing the generator is what makes the
work reproducible, and it is also what makes a determined adversary able to train
against it. That trade is taken deliberately in favour of reproducibility, and
stated rather than hidden.

---

## 5. Determinism is what makes the claim checkable

The contamination argument is only as good as the reproducibility of generation.
If `generate_env(seed, spec)` were not byte-identical across processes and
machines, a published result could not be verified and the claim would be an
assertion.

[SPEC-002](../specs/SPEC-002-env-generator.md) therefore requires determinism
stricter than "uses a seed":

- Byte-identical `canonical()` output across **separate subprocesses** (AC-1).
- The same under **different `PYTHONHASHSEED` values** — no reliance on hash
  ordering (AC-2).
- Byte-identical across **Windows and Linux** — no path-separator or newline
  leakage (AC-7).
- **No I/O, no clock, no global RNG** (AC-5). File metadata uses a generation-order
  `modified_tick`, never a timestamp, so output does not depend on when it ran.

Committed golden digests act as a tripwire: any change to fixtures or generation
logic breaks them, forcing a conscious decision about whether previously
published results remain comparable.
