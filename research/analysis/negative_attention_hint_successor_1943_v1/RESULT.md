# Successor #1958 result

## H/T/D/C/U

- **H**: advisory LOW_PRIORITY hints can guide attention without losing relevant evidence when raw observation remains authoritative.
- **T**: deterministic 32x20 fixture with toolbar, target, effect, decorative, and deliberately changed low-priority regions; compare FULL, ADVISORY_LOW_PRIORITY, and FORCED_EXCLUSION.
- **D**: 5 frozen cases × 3 modes = 15 rows, exact reconstruction flags, and SHA-256 source digest.
- **C**: FULL and advisory modes exact on every case; forced exclusion exposes the negative control; no broad token/latency claim.
- **U**: model usability, automatic proposals, GUI correctness, latency, and transfer remain untested.

## Formal result

```text
FULL                  exact 5/5
ADVISORY_LOW_PRIORITY exact 5/5
FORCED_EXCLUSION      exact 3/5
rows                  15
source SHA-256        9626f2f243847dc3be0b4d92a07ff93c91bf559e54a6d07ea8984e12fa3b17ba
```

**Scoped outcome: PASS_ADVISORY_LOW_PRIORITY_HINT_SAFETY_SCOPED.**

The forced-exclusion control fails exactly when the deliberately low-priority region changes, demonstrating why LOW_PRIORITY must remain advisory. The experiment is synthetic and container/local-only; it made no model, GUI, network, or runtime calls.

