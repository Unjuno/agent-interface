# Successor #1958 result

## H/T/D/C/U

- **H**: advisory LOW_PRIORITY hints can guide attention without losing relevant evidence when raw observation remains authoritative.
- **T**: deterministic 32x20 fixture with toolbar, target, effect, decorative, and deliberately changed low-priority regions; compare FULL, ADVISORY_LOW_PRIORITY, and FORCED_EXCLUSION.
- **D**: 5 frozen cases × 3 modes = 15 rows, exact reconstruction flags, and SHA-256 source digest.
- **C**: FULL and advisory modes exact on every case; forced exclusion exposes the negative control; canonical package size must be smaller for a PASS; no broad token/latency claim.
- **U**: model usability, automatic proposals, GUI correctness, latency, and transfer remain untested.

## Formal result

```text
FULL                  exact 5/5, package bytes 1305
ADVISORY_LOW_PRIORITY exact 5/5, package bytes 1349, 1544, 1585, 1617, 1814
FORCED_EXCLUSION      exact 3/5, package bytes 1344, 1503, 1535
rows                  15
source SHA-256        9626f2f243847dc3be0b4d92a07ff93c91bf559e54a6d07ea8984e12fa3b17ba
```

**Scoped outcome: HOLD_NO_SIZE_GAIN.**

The forced-exclusion control fails exactly when the deliberately low-priority region changes, demonstrating why LOW_PRIORITY must remain advisory. The repaired harness derives patches from the authoritative source and records source/reconstruction hashes, but the canonical advisory package is larger than FULL in every tested case. The safety result is retained as exact-recovery evidence; no size-reduction claim passes. The experiment is synthetic and container/local-only; it made no model, GUI, network, or runtime calls.

