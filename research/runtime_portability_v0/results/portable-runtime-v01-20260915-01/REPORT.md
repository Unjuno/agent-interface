# Portable runtime v0.1 — retained repair result

**Result ID:** `portable-runtime-v01-20260915-01`  
**Source/plan freeze:** `09c20af6f1f652231f22e3f242fa850c161275e8`  
**Prior retained v0 result:** `a8a4670b3da4ba89f7ac333dc75cdb9eadc2c7ca`

## Disposition

**PASS_CONTRACT_REPAIR_AND_USAGE_LEDGER / TOKEN_EFFICIENCY_STILL_UNPROVEN**.

The v0 counterexample is now rejected with `release_all must be final operation`; `release_all` must also appear exactly once. The old valid 1,000-program corpus still round-trips with zero failures.

## Executed checks

- **27/27** deterministic unit tests passed.
- C0 total **400,110 bytes**; C1 total **84,310 bytes**.
- Serialization proxy reduction remains **78.93%**.
- Synthetic full Linux/Windows/macOS profiles still admit the same representative AST; synthetic unimplemented profiles still fail readiness.
- No model, GUI, OS input or network call occurred.

## Exact provider-usage seam

The new ledger validates the retained golden desktop v3 aggregate at source blob `e168a9bdc84fc6b807f4e90806ec7c501da89689` as exact provider usage: six independently exact successful tasks; 3 model/planner boundaries including preflight; 2 model-visible images; 27,892 input tokens; 7,936 cached input tokens; 477 output tokens; 132 reasoning output tokens.

This is **not** a codec comparison. The ledger deliberately reports `paired_token_efficiency_claim_available=false`; a proxy-only arm is ineligible for comparison (`exact_provider_usage_required`). The current retained baseline is about **4648.67 input tokens per successful task**, but no causal reduction claim follows from that normalization.

## What is now buildable

The product implementation can target a language-neutral contract instead of the current Python object graph. Backends must declare capture, keyboard/text, pointer, scroll, focus, geometry, monotonic clock, feedback and release-all support, with `unsupported`, `unknown` and `permission_required` remaining explicit.

Python is the executable oracle. It is not selected as the final runtime ABI. The next systems implementation must reproduce these vectors before adding native OS behavior.

## H/T/D/C/U

**H:** terminal-release repair plus a strict usage ledger closes two false-positive paths without changing valid codec semantics.  
**T:** fixed v0.1 source, 27 tests, one 1,000-program offline allocation, one read-only import of a pre-existing provider-usage aggregate.  
**D:** PASS for contract repair and usage-accounting gate; FAIL/UNPROVEN for actual provider-token savings and native three-OS support.  
**C:** compact text can reduce bytes but tokenize poorly; native APIs may expose missing focus/scaling/permission semantics; exact-token gains can disappear once definition/invalidation/relearning costs are included.  
**U:** no paired same-model codec allocation, no native Windows/macOS/Wayland run, Python microtiming only, one synthetic corpus.

## Next gate

The next token-efficiency experiment must be paired and same-model: same hidden office tasks, same images/state, same correctness scorer, C0 versus compact codec, with exact provider input/output/image usage and dictionary definition + invalidation cost included. Do not promote the 78.93% byte result as token savings.
