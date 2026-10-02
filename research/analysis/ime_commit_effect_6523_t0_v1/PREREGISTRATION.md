# Issue #6523 — synthetic IME phase/effect T0

## Status and scope

This is an additive, no-model/no-GUI T0 method experiment for Issue #6523. It tests whether a finite event-trace contract can distinguish composition preedit, committed field value, intentional submit, and independently observed application effect across four route representations. It does **not** execute an IME or establish Japanese/CJK, browser, OS, GUI, or user-facing behavior.

## H / T / D / C / U

- **H:** A phase-aware classifier can preserve the four distinct stages and avoid false submit/effect completion on composition confirmation, cancellation, delayed value update, stale focus, unavailable composition state, or absent/mismatched effect receipt. Raw Enter and symbolic-key-only baselines will conflate at least one stage in the frozen traces. Native fill is a strong comparator and may match the phase-aware route on its qualified cases.
- **T:** Freeze 12 event traces with independently declared input text, target/focus generation, expected committed text, deliberate-submit intent, application-effect value, and single-line/multiline context. Evaluate `RAW_ENTER`, `SYMBOLIC_ONLY`, `NATIVE_FILL`, and `PHASE_AWARE` as separate deterministic interpretations. Candidate sees route-visible events and expected text only where the route actually receives it; the oracle is scorer-only. Independently reconstruct each route result from the raw fixture. Include ordinary Latin, CJK candidate acceptance/cancel, delayed DOM/value update, visible-glyph/committed-value mismatch, focus replacement, unavailable composition, separate submit, missing/mismatched effect, and single-line native-form control.
- **D:** `PASS_METHOD_SCOPED` only if the raw-only auditor reconstructs every route×trace row and rejects all six frozen output corruptions; the phase-aware route must never label preedit as committed, submit without explicit submit intent, or report an effect without an exact independent effect receipt; non-IME and native single-line controls must retain their stipulated behavior. The hypothesis is supported only if at least one raw/symbolic trace falsely submits or reports completion and the phase-aware route does not, while native fill remains explicitly compared. Any phase/effect conflation or audit disagreement is FAIL/STOP as specified; no model or product claim follows.
- **C:** The fixture semantics are authored, and a deterministic interpreter cannot prove any browser/IME emits these sequences. Native fill may be safer or faster; browser/app handlers may already suppress Enter during composition. Abstract costs are not time measurements.
- **U:** Real IME event order, actual committed Unicode value, runtime route support, application persistence, and user benefit remain untested; T1 requires an IME-capable disposable GUI host and an independent saved/server-side effect oracle.

## Frozen representation

Source: `cases.json`, schema `ime-commit-effect-cases-v1`. It stores only synthetic events and oracle labels; no real text, credentials, messages, or network state. Four route IDs are fixed. Candidate and auditor use only Python's standard library. The candidate writes a canonical JSON row set. The auditor independently derives expected outputs and ignores candidate aggregate summaries.

Construction tests may be corrected before formal invocation. The construction suite is `python -B -m unittest discover -s /input -p test_method.py`; execute it in the network-disabled WSLc image before freeze. After source hashes and empty output paths are frozen, invoke the candidate exactly once in a network-disabled WSLc container; only on exit 0 invoke the independent auditor exactly once in a second network-disabled WSLc container with raw input read-only. No retry, no threshold tuning, no GUI/IME, GPU, model, Docker/Podman, network, or external effect. WSLc memory flags are requests only; no enforcement claim.

## Decision outputs

`PASS_METHOD_SCOPED` describes only reconstruction of this synthetic finite contract. `H_SUPPORTED_METHOD_ONLY` means the declared synthetic route contrast appeared; it is not empirical route efficacy. Any T1 transfer is a separately preregistered allocation after ownership, GUI/IME capability, route equivalence, exact text and independent effect-oracle review.
