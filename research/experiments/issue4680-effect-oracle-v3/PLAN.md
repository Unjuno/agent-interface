# Successor allocation: explicit postcondition semantics v3

## H / T / D / C / U (frozen before execution)

- **H:** The predecessor fixture's `effect` values represent persistent desired postconditions, not necessarily state deltas. An independent transition oracle that derives the postcondition for `NO_ACTION` from the requested intent and current state can validate every retained proposal without consulting that expected-effect label during derivation.
- **T:** Read-only audit of the one previously consumed, frozen 10-row result. Recompute actions over a separate in-memory settings model. For `NO_ACTION`, resolve intent to a known field and emit its current persisted value only when it equals the requested value. For SET_FIELD, stage only; for visible toggle click, flip; for Save, commit the single staged supported value. YIELD remains no-op. Enforce proposal equality and the linked field→save path. Test expected-label corruption, wrong target, missing row, and broken multi-step controls.
- **D:** PASS only with exact source/predecessor identity, 10/10 proposal equality, 10/10 independently derived postconditions, valid linked sequence, 4/4 adversarial controls rejected, and all nine tests passing. This is a new postcondition-semantics audit allocation; v2 remains an immutable FAIL and is reported alongside it.
- **C:** Same frozen settings contract and retained proposal result as allocations #4680 construction v1 and effect-oracle v2. No model, optimizer, GUI, host input, network, GPU, or change to predecessor artifacts.
- **U:** Offline deterministic replay transition consistency only; no real app effects, Astra/Needle evidence, model speed, amortization, broad correctness, or full #4680 PASS.

## Execution boundary

One fresh local Docker invocation, exact locally cached `python:3.11-slim` image ID, network disabled, 1 CPU, 128 MiB, 16 PIDs, read-only source/root, 16 MiB bounded tmpfs, dropped capabilities and no-new-privileges. Predecessor inputs are read-only; only a fresh output directory is writable. No retry/tuning after first invocation.

