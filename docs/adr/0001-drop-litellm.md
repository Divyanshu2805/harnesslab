# ADR 0001 — Drop LiteLLM; use Inspect's native providers

**Status:** Accepted · **Date:** 2026-08-09

## Context

The original plan specified "Inspect's providers + LiteLLM fallback", on the
assumption that Inspect lacked native support for OpenRouter and Cerebras.

Checking the current provider list showed that assumption is wrong. Inspect
natively supports `groq/`, `google/`, `mistral/`, `ollama/`, and `openrouter/`.
Cerebras has no native provider but exposes an **OpenAI-compatible endpoint**,
which Inspect reaches through its built-in `openai-api/<provider>/<model>` path
using `CEREBRAS_API_KEY` and `CEREBRAS_BASE_URL`.

So every model on the board is reachable without a translation layer.

## Decision

**No LiteLLM.** Providers are addressed natively; Cerebras via
`openai-api/cerebras/<model>`.

## Consequences

**Good.** One less dependency, and — more importantly — **one source of truth for
token accounting**. LiteLLM and Inspect each normalise usage reporting in their
own way, and this project's entire cost model is built on token counts. Two
reporting paths would have meant a class of quiet discrepancy in exactly the
numbers the paper publishes.

**Cost.** If a future provider is neither native nor OpenAI-compatible, it must
be added as an Inspect provider extension rather than picked up free. Acceptable:
the OpenAI-compatible shape is now close to universal, and adding a provider is a
bounded task.

**Enforced.** [SPEC-011 AC-7](../../specs/SPEC-011-multi-provider-runner.md)
asserts LiteLLM is absent from the dependency tree, so it cannot creep back in as
a transitive convenience.

## Alternatives rejected

**Keep LiteLLM as a safety net.** Dependencies that exist "just in case" get used
by accident, and this one would have undermined token accounting the first time
someone routed a call through it.

**Write a thin provider abstraction of our own.** All the maintenance of a
translation layer, none of the ecosystem.
