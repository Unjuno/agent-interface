# Issue #3190 — current-main desktop lifecycle source rebind audit

Allocation: `desktop-lifecycle-rebind-3190-20260922-01`
Branch: `research/desktop-lifecycle-rebind-3190-20260922-v1`
Additive path: `research/integration/desktop_lifecycle_rebind_3190_v1/`
Intake main: `74d0ebb63c880fc5818bc4bbe6bb0c6b08579d39`

## H

The four-source lifecycle contract retained by #2259 can be rebound to current main by changing only the declared `runtime/cli_v1/api.py` source identity while preserving the exact source set/roles, the ten lifecycle rows, zero authority grants, and fail-closed outcome distinctions. Any undeclared source, role mutation, row mutation, or authority-count mutation remains detectable.

This is a source/provenance hypothesis only. It does not establish live adapter, GUI, model, input, task-effect, latency, token, or production behavior.

## T

- Preserve the predecessor `golden_cli_lifecycle_contract_successor_2259_v1` files unchanged.
- Pin current main `74d0ebb63c880fc5818bc4bbe6bb0c6b08579d39` and exactly four current source Git blobs.
- Predecessor source set/roles are unchanged. Three blob identities must remain identical. Only `runtime/cli_v1/api.py` may change from predecessor blob `f9dc26441c5f4ff9d7f57aa6a6a7b3849a1537d7` to the frozen current blob.
- The independent auditor recomputes each Git blob identity from checked-out bytes without importing candidate runtime code, parses Python sources only as syntax/role evidence, and compares the ten lifecycle rows byte-semantically against the predecessor result.
- Five copied-evidence corruption controls: changed source hash, undeclared fifth source, role mutation, lifecycle-row mutation, authority-count mutation. Every control must reject.
- One formal source-only audit invocation after public freeze; zero formal reruns/tuning/replacements. No GUI/model/input/network experiment.

## D

`PASS_DESKTOP_VERTICAL_SLICE_REBOUND_AUDIT_SCOPED` iff:

1. all four frozen current source bytes recompute to their declared Git blob IDs;
2. source path and role sets exactly equal the predecessor contract;
3. exactly one source identity changed, and it is the declared `runtime/cli_v1/api.py` rebind;
4. the API still exposes diagnostic-only doctor, dispatch, and cleanup/finally semantics; core/golden source roles remain present;
5. all ten lifecycle rows are identical to the predecessor result and appear exactly once in the fixed order;
6. authority grants, model calls, GUI calls, input calls, and network calls are all zero;
7. all five corruption controls reject;
8. frozen experiment source/gates remain unchanged.

Use `FAIL_MANIFEST_REBIND_SCOPE` for an undeclared source/role/semantic change, `HOLD_SOURCE_DRIFT_UNRESOLVED` for unmatched source bytes, `HOLD_LIFECYCLE_EVIDENCE_INCOMPLETE` for missing rows/authority accounting, and `STOP_DESKTOP_AUDIT_RUNNER` for execution/provenance failure.

## C

The predecessor lifecycle table is itself a static contract. Equality of its rows plus source-role preservation does not prove those rows are exercised by current live runtime. A later current-main live integration allocation remains necessary.

## U

No provider/model, GUI/input, application effect, X11/Windows/macOS backend execution, performance, tokens, human tempo, or production acceptance is measured. CPython version differences are irrelevant to the byte/JSON/AST checks but are retained in environment provenance.

## Roadmap

1. collision/source review;
2. excluded synthetic construction tests;
3. public source/gate freeze;
4. one source-only formal audit;
5. independent corruption controls and raw result retention;
6. additive PR and exact-main readback;
7. close only #3190 if the scoped audit and delivery gates pass; broader #2789 remains open.
