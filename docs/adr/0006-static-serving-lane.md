# ADR 0006 — Static serving lane; the expensive path is structurally unreachable

**Status:** Accepted · **Date:** 2026-08-09

## Context

The project must cost $0 indefinitely, including after active work stops. A
public leaderboard that can trigger computation is a standing liability: quota
exhaustion, a surprise bill, or an abuse vector.

The usual answer is rate limiting on the request path. That is a **configuration
setting**, and configuration settings get misconfigured, bypassed by a new
endpoint, or forgotten during a refactor.

## Decision

Two lanes with **no code path between them**:

- **Evaluation lane** — scheduled GitHub Actions and local GPU sweeps. Holds all
  provider credentials. Cannot be triggered by the public.
- **Serving lane** — GitHub Pages. Prebuilt static HTML and JSON, charts rendered
  client-side. No backend, no database connection, no model call.

A visitor cannot cause a model call **because no such path exists**, not because
something declined the request.

## Consequences

**Good.** Cost is bounded by construction. The site cannot sleep (no idle
suspend), cannot be scraped into a bill, and keeps working indefinitely after the
project is abandoned. GitHub Actions on standard runners is free and unmetered
for public repositories, so CI is genuinely $0 too.

**Good, and worth saying in interviews.** *"The expensive path is structurally
unreachable from the internet"* is an architecture decision. *"We added a rate
limiter"* is a config change. The first survives a refactor; the second is one
careless PR from being wrong.

**Enforced, not assumed.**
[SPEC-020 AC-2](../../specs/SPEC-020-leaderboard.md) scans built output for
provider endpoints and keys; AC-8 scans for secrets and connection strings.

**Cost.** No dynamic querying — a visitor cannot run an arbitrary filter
server-side. Mitigated by shipping the full result JSON and filtering
client-side, which is entirely adequate at this data scale.

**Cost.** Every leaderboard update requires a CI build and deploy. Fine for a
nightly cadence, and it means the published state always corresponds to a commit.

## Alternatives rejected

**A small backend with rate limiting.** Enables dynamic queries. Requires
hosting that sleeps on free tiers, introduces a request path to credentials, and
makes cost a function of traffic. Every failure mode this decision exists to
remove.

**Serverless functions for queries.** Same objection with better ergonomics: cost
still scales with traffic and a credential path still exists.

**Client-side calls with a public key.** A public key is a public key.
