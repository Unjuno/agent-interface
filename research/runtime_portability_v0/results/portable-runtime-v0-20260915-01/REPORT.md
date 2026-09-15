# Portable runtime v0 — retained first result

**Result ID:** `portable-runtime-v0-20260915-01`  
**BASE:** `a74c5cb704c17bc63e6d73aa98a4bac62d738c47`  
**Source/plan freeze:** `17594805050f3c684ed397a7cc118f11f4ef346b`  

## Disposition

**PASS_SCOPED_CODEC_AND_PORTABILITY_MODEL / REPAIR_CONTRACT_TERMINAL**.

The frozen 1,000-program comparison passed all semantic round trips and the same
representative program admitted under synthetic fully-capable Linux, Windows and
macOS profiles. This demonstrates that the *contract representation* is not tied
to one OS. It is not native backend evidence.

A post-result static audit found one contract weakness: `release_all` is required
somewhere and held state must be empty at the end, but v0 does not require the
release marker itself to be the terminal operation. The first outcome is retained
unchanged. A successor must require `release_all` as the final operation and add
a regression; do not rewrite this result.

## Frozen experiment

- Unit tests before allocation: **20 passed, 0 failed**.
- Corpus: **1000** deterministic office-like programs, seed `20260915`.
- C0/C1 round-trip failures: **0**.
- C0 total: **400,110 UTF-8 bytes**.
- C1 total: **84,310 UTF-8 bytes**.
- Serialization-proxy reduction: **78.93%** total.
- Median C0/C1: **388 / 86 bytes** (**77.84%** median reduction).
- Median decode diagnostic on this host: C0 **8.145 µs**, C1 **10.009 µs** per program. C1 was about **22.9%** slower to decode in this Python oracle; this is not a product benchmark.
- Provider token accounting: **UNAVAILABLE**. Bytes are not tokens.

## Persistent dictionary proxy

The exact `save` workflow definition was 71 bytes plus references. At every tested
lifetime (1, 2, 4, 8, 16, 32, 64 uses) the definition+reference byte count was
smaller than repeating canonical C0. The first tested byte-proxy break-even was
1 use. This is an intentionally small exact workflow and **must not be generalized
to provider-token break-even or arbitrary workflows**.

| Uses | C0 bytes | C2 definition + refs | Delta |
|---:|---:|---:|---:|
| 1 | 409 | 136 | -273 |
| 2 | 818 | 201 | -617 |
| 4 | 1636 | 331 | -1305 |
| 8 | 3272 | 591 | -2681 |
| 16 | 6556 | 1123 | -5433 |
| 32 | 13132 | 2195 | -10937 |
| 64 | 26284 | 4339 | -21945 |

## Platform result

Synthetic fully-capable Linux/X11, Windows/Win32 and macOS/Quartz manifests admit
the same AST. Synthetic unimplemented Linux/Wayland, Windows-native and
macOS-native manifests correctly fail office-readiness instead of being silently
treated as supported.

This is the desired failure semantics for later real backends. No native Windows,
macOS or Wayland API was invoked in this allocation.

## H/T/D/C/U

**H:** a small common contract and replaceable codec can preserve semantics across
OS profiles while removing repeated serialization.  
**T:** frozen source, 20 tests, one 1,000-program deterministic allocation, no
model/GUI/OS input/network.  
**D:** codec round trips PASS; synthetic representation portability PASS; product
backend support remains UNPROVEN; terminal release contract requires REPAIR.  
**C:** byte reduction may not map to model-token reduction; native backends may
expose missing semantics; persistent definitions may have larger real setup and
invalidation cost.  
**U:** no provider tokenizer/API accounting, no native OS execution, uncontrolled
CPU clocks, one synthetic corpus.

## Next bounded successor

1. Repair terminal release position and regenerate conformance vectors under a new result ID.
2. Add a provider-usage ledger seam so exact model input/output/image tokens can be attached without entering the semantic core.
3. Implement one native backend only after the repaired contract is accepted; use that backend as the first real conformance target before duplicating work across all OSes.
