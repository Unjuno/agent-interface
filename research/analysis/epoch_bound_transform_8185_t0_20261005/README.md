# Issue #8185 T0: epoch-bound frame transform composition

This finite synthetic experiment compares a direct last-known transform with a typed, epoch-bound transform graph for mapping target and action geometry into a current input frame. It tests method semantics only. It makes no claim about a GUI, native DPI APIs, user data, OS input, latency, or product behavior.

The formal package lives under `results/FORMAL_A01/`. The candidate process receives only `public/cases.jsonl`; hidden truth and intended/forbidden labels are mounted only for the auditor. `src/test_construction.py` is pre-freeze construction validation and is not formal evidence.

## Reproduction

Run exactly the commands recorded in `results/FORMAL_A01/RUN_FREEZE.json`, using its pinned source SHA and OCI image digest. The formal candidate and auditor each have one invocation. Do not rerun a consumed allocation; make a new allocation/version for any repair.

## Scope

The positive discriminator is composition through separately versioned frame edges across mixed-DPI and epoch transitions. Shared uncertainty and independent error are controls. The baseline has the latest direct transform where available and abstains when composition is required. Invalid, stale, ambiguous, mismatched, or unmodeled chains must fail closed.
