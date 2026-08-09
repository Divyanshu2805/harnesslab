#!/usr/bin/env python
"""Probe live provider quotas and regenerate docs/PROVIDERS.md.

Free tiers change monthly -- Google cut theirs by 50-80% in December 2025 -- and
the entire sweep plan is sized from these numbers. A quota table written once
and trusted thereafter is how a project discovers in week four that week two's
arithmetic was wrong.

    uv run python scripts/verify_providers.py --check        # fail on drift
    uv run python scripts/verify_providers.py --write-docs   # regenerate the table

Most providers publish their limits in response headers, so a probe reads them
from a deliberately tiny request. Google does not, and is marked unverifiable
rather than silently assumed correct.

Cost: one ~10-token completion per provider. Negligible, but real -- once
SPEC-006 exists this books a named ledger reservation.

Never prints a key. Failures report the provider and status code only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from harnesslab.providers import ProbeResult, QuotaLimits, registry
from harnesslab.providers.registry import get

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "PROVIDERS.md"
TIMEOUT = 30.0

# Providers publish limits under inconsistent header names. Groq sends
# `x-ratelimit-limit-requests` meaning per DAY while `-tokens` means per MINUTE;
# Cerebras suffixes the window explicitly. Parse both shapes.
_HEADER = re.compile(
    r"^x-ratelimit-limit-(?P<what>requests|reqs|req|tokens)"
    r"(?:-(?P<window>minute|hour|day))?$",
    re.I,
)
_CANON = {"req": "requests", "reqs": "requests", "requests": "requests", "tokens": "tokens"}

# Where a provider omits the window, this is what it means.
_DEFAULT_WINDOW = {"groq": {"requests": "day", "tokens": "minute"}}


def _limits_from_headers(headers: dict[str, str], provider: str, source: str) -> QuotaLimits | None:
    found: dict[str, int] = {}
    for name, raw in headers.items():
        m = _HEADER.match(name)
        if not m:
            continue
        try:
            value = int(float(raw))
        except ValueError:
            continue
        # Providers use negative sentinels for "no limit" / deprecated fields.
        # OpenRouter returns -1 with an explicit "safe to ignore" note.
        if value < 0:
            continue
        what = _CANON[m.group("what").lower()]
        window = (m.group("window") or "").lower()
        if not window:
            window = _DEFAULT_WINDOW.get(provider, {}).get(what, "")
        if not window:
            continue
        found[f"{what}_per_{window}"] = value

    if not found:
        return None
    try:
        return QuotaLimits(
            requests_per_minute=found.get("requests_per_minute"),
            requests_per_day=found.get("requests_per_day"),
            tokens_per_minute=found.get("tokens_per_minute"),
            tokens_per_day=found.get("tokens_per_day"),
            source_url=source,
            fetched=dt.date.today(),
        )
    except Exception:
        return None


def _chat_probe(
    *, key: str, url: str, model: str, api_key: str, provider: str, source: str
) -> ProbeResult:
    """One minimal completion, read the rate-limit headers off the response."""
    try:
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            },
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as exc:
        return ProbeResult(model_key=key, reachable=False, error=f"{type(exc).__name__}")

    if resp.status_code >= 400:
        return ProbeResult(
            model_key=key,
            reachable=False,
            error=f"HTTP {resp.status_code}",
            note=resp.text[:160] if resp.status_code != 401 else "auth rejected",
        )

    observed = _limits_from_headers(dict(resp.headers), provider, source)
    return ProbeResult(
        model_key=key,
        reachable=True,
        observed=observed,
        note=None if observed else "reachable, but publishes no rate-limit headers",
    )


def probe_openrouter(key: str) -> ProbeResult:
    """OpenRouter exposes limits on a dedicated endpoint, costing no tokens."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return ProbeResult(model_key=key, reachable=False, error="OPENROUTER_API_KEY unset")
    try:
        resp = httpx.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json().get("data", {})
    except (httpx.HTTPError, ValueError) as exc:
        return ProbeResult(model_key=key, reachable=False, error=type(exc).__name__)

    # `rate_limit` is documented by OpenRouter as deprecated and returns -1;
    # do not read a quota out of it. The daily cap depends on account state and
    # is not exposed here, so it stays as declared from the docs.
    free_tier = data.get("is_free_tier", True)
    tier = (
        "no credits purchased -- 50 req/day tier"
        if free_tier
        else "credits purchased -- ~1,000 req/day tier"
    )
    return ProbeResult(model_key=key, reachable=True, observed=None, note=tier)


def probe_ollama(key: str) -> ProbeResult:
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    try:
        resp = httpx.get(base.rstrip("/") + "/models", timeout=10.0)
        resp.raise_for_status()
        payload = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        return ProbeResult(
            model_key=key, reachable=False, error=f"{type(exc).__name__} (is ollama running?)"
        )
    # `data` can be absent or explicitly null on an Ollama with nothing pulled.
    models = (payload or {}).get("data") or []
    if not models:
        return ProbeResult(
            model_key=key,
            reachable=True,
            note="local server up but NO models pulled -- SPEC-010 needs them by day 8",
        )
    return ProbeResult(
        model_key=key, reachable=True, note=f"local server up, {len(models)} model(s) pulled"
    )


PROBES = {
    "groq-llama-8b": lambda k: _chat_probe(
        key=k,
        url="https://api.groq.com/openai/v1/chat/completions",
        model="llama-3.1-8b-instant",
        api_key=os.environ.get("GROQ_API_KEY", ""),
        provider="groq",
        source=get(k).limits.source_url,
    ),
    "groq-llama-70b": lambda k: _chat_probe(
        key=k,
        url="https://api.groq.com/openai/v1/chat/completions",
        model="llama-3.3-70b-versatile",
        api_key=os.environ.get("GROQ_API_KEY", ""),
        provider="groq",
        source=get(k).limits.source_url,
    ),
    "cerebras-gpt-oss-120b": lambda k: _chat_probe(
        key=k,
        url=os.environ.get("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1").rstrip("/")
        + "/chat/completions",
        model="gpt-oss-120b",
        api_key=os.environ.get("CEREBRAS_API_KEY", ""),
        provider="cerebras",
        source=get(k).limits.source_url,
    ),
    "mistral-small": lambda k: _chat_probe(
        key=k,
        url="https://api.mistral.ai/v1/chat/completions",
        model="mistral-small-latest",
        api_key=os.environ.get("MISTRAL_API_KEY", ""),
        provider="mistral",
        source=get(k).limits.source_url,
    ),
    "openrouter-free": probe_openrouter,
    "qwen25-7b": probe_ollama,
}


def probe_all() -> dict[str, ProbeResult]:
    results: dict[str, ProbeResult] = {}
    for key, fn in PROBES.items():
        print(f"  probing {key} ...", end=" ", flush=True)
        r = fn(key)
        results[key] = r
        if not r.reachable:
            print(f"UNREACHABLE ({r.error})")
            if r.note:
                print(f"      {r.note}")
        elif r.observed:
            print("ok, limits read from headers")
        else:
            print(f"ok ({r.note})")
    return results


def render_docs(results: dict[str, ProbeResult]) -> str:
    today = dt.date.today().isoformat()
    rows: list[str] = []
    for spec in sorted(registry().values(), key=lambda m: (m.lane, m.key)):
        lim = spec.limits
        r = results.get(spec.key)
        if r is None:
            status = "not probed"
        elif not r.reachable:
            status = f"unreachable ({r.error})"
        elif r.observed:
            status = "**live-verified**"
        elif not lim.probe_supported:
            status = "not probeable"
        else:
            status = "no headers"

        def fmt(v: int | None) -> str:
            return f"{v:,}" if v else "—"

        per_day = lim.trajectories_per_day()
        rows.append(
            f"| `{spec.key}` | {spec.display_name} | {fmt(lim.requests_per_minute)} "
            f"| {fmt(lim.requests_per_day)} | {fmt(lim.tokens_per_minute)} "
            f"| {fmt(lim.tokens_per_day)} | {fmt(lim.context_ceiling)} "
            f"| {'∞' if per_day is None else f'{per_day:,}'} | {lim.fetched} | {status} |"
        )

    unreachable = [k for k, r in results.items() if not r.reachable]
    warn = ""
    if unreachable:
        warn = (
            "\n> [!WARNING]\n> Unreachable at last probe: "
            + ", ".join(f"`{k}`" for k in unreachable)
            + ".\n> Sweep sizing that depends on these is unconfirmed.\n"
        )

    # Sources are rendered from the registry, so a quota can never appear
    # without the page it was read from (SPEC-001 AC-3).
    sources = "\n".join(
        f"- `{k}` — <{u}>"
        for k, u in sorted({m.key: m.limits.source_url for m in registry().values()}.items())
    )

    return f"""# Provider free tiers

<!-- Generated by scripts/verify_providers.py. Do not hand-edit. -->
**Last probed: {today}**

Free tiers change monthly — quotas move, models are withdrawn, whole tiers
disappear. Nobody maintains a current, sourced comparison of what you can
actually run an agent on for free, so this table is a small standalone
contribution as well as an input to the experiment.

Every row carries a **fetch date** and a **source URL**, enforced by
[SPEC-001 AC-3](../specs/SPEC-001-provider-registry.md).
{warn}
## The table

| key | model | RPM | RPD | TPM | TPD | ctx cap | traj/day | fetched | probe |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
{chr(10).join(rows)}

**`traj/day` is the number that matters.** Raw quota figures mislead for agentic
work, because a trajectory is many calls that each resend the accumulated
history. Groq's 70B reads as generous at 1,000 requests/day and is really about
six trajectories, because 100K tokens/day binds first. See
[TOKEN_BUDGET.md](TOKEN_BUDGET.md).

## Sources

{sources}

## Probe status, and what it means

- **live-verified** — limits were read from the provider's own response headers
  at the date above.
- **not probeable** — the provider does not publish limits in headers. Google
  exposes them only in AI Studio, so drift there has to be caught by hand. The
  figures are from the source URL and are trusted, not confirmed.
- **unreachable** — the probe failed. Either the key is unset, or the tier has
  changed. Investigate before sizing anything on that row.

## Things worth knowing before you plan around these

**Google cut free-tier quotas by 50-80% in December 2025.** Any tutorial
predating that is stale, often by a large factor. This is the most common source
of wrong capacity assumptions.

**Groq's 70B is effectively unusable for agents on the free tier.** 1,000
requests/day reads as generous; 100K tokens/day is the real ceiling. It is on the
board for the model-size axis at disclosed low N, not as a workhorse.

**Cerebras binds on two dimensions at once.** 1M tokens/day is the most generous
quota here, but the **8,192-token context ceiling** is the constraint that shapes
the whole experiment: it is why every cell in the pooled grid runs a capped
context policy, and therefore why the compaction ablation exists
([adr/0008](adr/0008-shared-context-policy.md)).

**OpenRouter's daily limit depends on account state** — 50 requests/day without
purchased credits. The `:free` roster also shifts continuously, which makes it
unsuitable as a stable axis.

**Cerebras has no native Inspect provider.** It is reached through Inspect's
OpenAI-compatible path as `openai-api/cerebras/<model>`, which is why this
project has no LiteLLM dependency ([adr/0001](adr/0001-drop-litellm.md)).

**Rate limits are per organisation, not per key.** More keys do not mean more
quota.

## Lane A: local models

Lane A has no quota, so its constraints are different in kind: **VRAM residency**
and **throughput**. An 8 GB card at 4-bit tops out around 12B; a model that
spills into system RAM collapses to CPU-like speeds.

Identity here is the **digest**, never the tag
([adr/0011](adr/0011-pin-model-digests.md)). Digests and measurements are filled
in by [SPEC-010](../specs/SPEC-010-lane-a-model-gate.md) on day 8; until then the
pooled grid is not sweep-ready and `assert_sweep_ready()` refuses to run.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit non-zero on drift")
    ap.add_argument("--write-docs", action="store_true", help="regenerate docs/PROVIDERS.md")
    args = ap.parse_args()

    print("Probing providers (one tiny request each) ...")
    results = probe_all()

    print("\nDrift against the registry:")
    drifted = False
    for key, result in results.items():
        declared = get(key).limits
        diffs = result.drift_against(declared)
        if diffs:
            drifted = True
            print(f"  DRIFT {key}:")
            for d in diffs:
                print(f"    {d}")
    if not drifted:
        print("  none detected on probeable fields")

    unreachable = [k for k, r in results.items() if not r.reachable]
    if unreachable:
        print("\nUnreachable:")
        for k in unreachable:
            print(f"  {k}: {results[k].error}")

    if args.write_docs:
        DOCS.write_text(render_docs(results), encoding="utf-8", newline="\n")
        print(f"\nwrote {DOCS.relative_to(ROOT)}")

    if args.check and (drifted or unreachable):
        print("\nFAIL: quota drift or unreachable provider. Re-check sweep sizing.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
