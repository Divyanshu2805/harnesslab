---
spec: NNN
title: <short imperative title>
status: Draft          # Draft | Approved | In Progress | Accepted
depends_on: []         # spec IDs, e.g. [002, 003]
day: N                 # scheduled day from the roadmap
---

# SPEC-NNN
## Motivation

Why this exists and what breaks without it. One or two paragraphs. If this spec
makes or implements a methodological commitment, link the relevant document in
`../docs/` rather than restating the argument here.

## Scope

**In scope**

- …

**Out of scope**

- … (name the things a reader would reasonably expect here but will not find,
  and say which spec owns them instead)

## Interface contract

The public surface this spec creates: signatures, Pydantic models, invariants
that callers may rely on. Enough that a dependent spec can be written against it
without reading the implementation.

```python
# illustrative
```

**Invariants**

- …

## Design notes

Key decisions and, explicitly, the alternatives rejected. A reader six months
from now should be able to tell whether a surprising choice was deliberate.

## Acceptance criteria

Numbered, individually falsifiable, each demonstrable by a test.

- **AC-1.** …
- **AC-2.** …

## Test plan

| Level | What it covers |
|---|---|
| unit | … |
| golden | … |
| integration | … |

Note which markers apply (`network`, `gpu`, `slow`) and confirm that the default
offline path still covers the acceptance criteria.

## Definition of done

- [ ] `make check` green
- [ ] Every AC demonstrated by a named test
- [ ] Docs updated in the same change: …
- [ ] Status set to `Accepted`
