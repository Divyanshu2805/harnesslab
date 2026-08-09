# Publication workstream

Tracked from **Day 15**, not assembled at the end. This is the difference between
having a project and having a publication, and it is the part of a plan most
easily dropped — it has no daily deliverable until very late, so it disappears
unless it is scheduled like everything else.

---

## 1. Day 15 — request arXiv endorsement

**This is the item with the longest lead time and the least control.**

First-time submitters to `cs.LG` need an endorsement from an existing author.
Institutional email sometimes auto-endorses, but a **post-graduation address may
no longer qualify** — which is exactly the situation to discover three weeks
early rather than three days before submission.

- **When:** Day 15. Endorsement requests sit in inboxes for weeks.
- **Who:** the MITACS supervisor at Calgary is the natural ask.
- **Slack:** three weeks before the paper is ready on Day 36.

### If it does not arrive

The project does not stall. The blog post and the HuggingFace dataset release
ship on schedule and carry the traction, and the paper goes to **TMLR**, which
requires no endorsement and which is in any case the better venue for a careful
null result. Endorsement is a convenience, not a dependency.

---

## 2. Two documents, not one

Same work, two audiences. Neither substitutes for the other.

| | **Paper** | **Blog post** |
|---|---|---|
| Length | 5–6 pages | ~1,500 words |
| Format | LaTeX, `paper/` | Markdown, on the Pages site |
| Reader | Reviewers, researchers, admissions committees | r/LocalLLaMA, Hacker News, practitioners |
| Leads with | The estimand, the design, the interval | *"Which agent setups actually work on a GPU you own?"* |
| Day | 36 | 37 |

The blog post is what gets linked and shared, and traction is a real signal a
paper alone does not produce. It must be **standalone** — comprehensible without
the paper — and link the leaderboard, the dataset, and the repo.

---

## 3. Figures are built once, on Day 24

[SPEC-021](../specs/SPEC-021-charts.md) exports **vector PDF for the paper and
JSON for the web from a single chart definition**.

Rebuilding figures during the endgame is the classic way a deadline slips, and
figures redone under pressure drift from the web versions they were meant to
match. Building both targets on Day 24 costs a little more then and removes an
entire category of endgame work.

**No screenshots. No rasterised charts.**
([SPEC-030 AC-2](../specs/SPEC-030-publication.md))

---

## 4. Numbers are generated, never typed

Every number in the results section comes from a generated LaTeX macro file
produced by the statistics module. A hand-typed number is a number that can
silently disagree with the artifact it claims to summarise, and this project's
whole argument is that its numbers are traceable.

[SPEC-030 AC-3](../specs/SPEC-030-publication.md) scans the results section for
numerals and checks them against the macro file.

---

## 5. Positioning

Prior work is **named and credited**, and the gap is stated specifically:

> HAL, AstaBench, τ-bench, AgentBench, GAIA, WebArena, and the ReAct /
> Reflexion / plan-and-solve papers.

Two rules, both non-negotiable:

- **No claim of novelty that overlaps HAL without acknowledging it.** HAL already
  argues that cost is systematically omitted from agent leaderboards. This work
  tests a stronger version of that claim; it does not discover it.
- **The words "novel" and "first-ever" do not appear.** Locate the prior work,
  name the specific gap, state the design, report what was measured.

`RELATED_WORK.md` gets **two dedicated days (20–21)**, running in parallel with
infrastructure work. Positioning honestly against seven bodies of prior work is
real reading, not a paragraph written during the writeup.

---

## 6. Required content

Beyond the results, the paper must contain:

- **The pre-registration commit hash**, and which of the three pre-declared
  outcomes obtained ([PREREGISTRATION.md](PREREGISTRATION.md)).
- **The suppression estimate in the abstract** — if the 8K context cap depressed
  the reflective harnesses, the headline is a directional lower bound and a
  reader must not be able to miss that.
- **The MDE from the Day 20 power check**, regardless of outcome. Without it a
  null result is uninterpretable.
- **Limitations**, stated plainly: small local models, low N on quota-starved
  providers, single-coder intra-rater κ, the task constraints imposed by
  deterministic scoring, and any quantisation confound arising from
  [SPEC-010](../specs/SPEC-010-lane-a-model-gate.md).

---

## 7. Timeline

| Day | Item |
|---|---|
| 15 | arXiv endorsement request sent |
| 20–21 | Related-work reading (parallel with infrastructure) |
| 24 | Figure pipeline built — both render targets |
| 32 | Headline finding available |
| 35 | HuggingFace dataset release, with DOI for citation |
| 36 | Paper draft, LaTeX, figures final |
| 37 | Blog post; publish; share |
| post | **TMLR submission** |

---

## 8. Artifacts a reader should be able to reach

| Artifact | Where |
|---|---|
| Paper | arXiv (`cs.LG`), then TMLR |
| Blog post | GitHub Pages site |
| Leaderboard | GitHub Pages site — live from Day 23 |
| Dataset + trajectories | HuggingFace, CC-BY-4.0 |
| Code | GitHub, Apache-2.0 |
| Pre-registration | A commit hash in this repository |
| Every published number | A row in the results store, traceable to a git SHA and a seed |
