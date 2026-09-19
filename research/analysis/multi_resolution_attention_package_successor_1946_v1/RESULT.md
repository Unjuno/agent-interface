# Issue #1946 analytical fixture result

Source: [Unjuno/agent-interface#1946](https://github.com/Unjuno/agent-interface/issues/1946).

## H/T/D/C/U

- **H**: a typed multi-resolution package can preserve exact task-relevant
  evidence while using less encoded observation data than FULL, provided the
  authoritative raw frame remains reconstructable from the deterministic base
  recipe and lossless patches.
- **T**: deterministic 64×40 synthetic GUI fixture with toolbar, dialog,
  tiny-status, and duplicate-label regions. Compare FULL, GLOBAL_LOW_ONLY,
  GLOBAL_LOW_PLUS_CANDIDATE, and GLOBAL_LOW_PLUS_CANDIDATE_PLUS_CRITICAL over
  unchanged, tiny-status, dialog, toolbar, and duplicate-label cases.
- **D**: 20 rows, SHA-256 source/reconstruction digests, exact reconstruction
  flags, and encoded package byte counts.
- **C**: FULL must reconstruct exactly; low-resolution-only must fail on a
  relevant high-frequency change; candidate and critical lossless patches must
  recover their selected relevant changes; at least one nontrivial exact arm
  must be smaller than FULL.
- **U**: regions are selected from frozen fixture truth, not automatically
  proposed; no model usability, token, latency, GUI correctness, or transfer
  claim is made.

## Result

```text
FULL                                  exact 5/5
GLOBAL_LOW_ONLY                      exact 1/5
GLOBAL_LOW_PLUS_CANDIDATE            exact 4/5
GLOBAL_LOW_PLUS_CANDIDATE_PLUS_CRITICAL exact 5/5
total rows                           20
FULL bytes                           2720
```

The exact multi-resolution arm reconstructs all five authoritative fixtures and
uses 762 bytes on the largest tested package, below the 2,720-byte FULL package.
The low-resolution-only arm loses relevant high-frequency changes. The
candidate arm handles ordinary changed regions, while the critical arm is
needed for the tiny-status case.

**Scoped outcome: PASS_MULTI_RESOLUTION_ATTENTION_PACKAGE_SCOPED.**

The result is an analytical fixture proof only. Candidate regions were derived
from fixture truth as explicitly allowed by #1946; automatic attention
discovery and model-facing benefit remain untested.

