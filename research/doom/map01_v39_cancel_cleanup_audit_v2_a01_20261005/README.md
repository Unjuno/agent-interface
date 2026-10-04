# Cancellation cleanup bracket audit v2 — A01

## Question and scope

**H:** A raw-only successor auditor can reject internally contradictory per-key cleanup samples and request/synchronization times while preserving the valid A03 fake-display result.

**T:** Apply a versioned supplemental auditor to the exact `candidate-events.jsonl` and `RESULT.json` from PR #7769 A03. Run deterministic mutations for unavailable/incorrect key states, reversed sample order, release request after the post sample, sync return outside request order, and bool-as-int interval endpoints. Each mutation recomputes the result's raw digest so rejection cannot be attributed only to a stale hash.

**D:** `PASS_RECONSTRUCTED_SCOPED` only for the exact raw/result pair with two matching per-key admissions/releases, confirmed sample states, exact integer sample endpoints, ordered request/sync/sample timestamps, consistent nested brackets and identities, verified neutral cleanup, and unchanged non-authority/non-consumption fields. Any mismatch is `FAIL_MISMATCH`.

**C:** The sample interval brackets cleanup; it does not identify the exact physical key-up edge. Independent sample truth is assumed from this frozen fake-display producer.

**U:** This repairs only a saved-result audit gap. It is fake-display construction evidence: no OS/game input, useful task feedback, threat response, recovery, or MAP01 result is established. Do not replace the immutable A03 auditor or reinterpret its original PASS; run this supplemental version alongside it.

## Inputs and provenance

The immutable fixtures are copied byte-for-byte from `Unjuno/agent-interface` PR #7769 head `32d67fa285d23f01235ade98168a3a5fe7422a48`, package `research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/results/a03/`. Candidate raw SHA-256 is `36b60282cfc2a7c328cdb7c62ec0d37b029808dc7cf2f6e327d0fd954fd3c99d`; `RESULT.json` SHA-256 is `063015f77f8ac6c94752b6f397a51ec4dfa74cc2715a5795ae163cd70d0cfcca`.

The historical auditor is preserved at that PR head with SHA-256 `b9b2bd5551be629a4ba949697aa5f9fa380df57c98a8c951f22c320925288a96`. A separate reviewer mutation against it changed a release pre-sample to `down: false`, placed `release_request_ns` after `post_sample.finished_ns`, recomputed the raw digest, and still obtained the old scoped PASS. This A01 leaves that source and result unchanged and adds the rejecting audit path here.

## Reproduction

From repository root, run:

```powershell
python research/doom/map01_v39_cancel_cleanup_audit_v2_a01_20261005/audit_v2.py > research/doom/map01_v39_cancel_cleanup_audit_v2_a01_20261005/AUDIT_V2.json
python -m unittest discover -s research/doom/map01_v39_cancel_cleanup_audit_v2_a01_20261005 -p test_audit_v2.py -v
```

The audit command prints a one-line JSON report; redirect it to `AUDIT_V2.json`. `test_audit_v2.py` covers the baseline and seven raw-digest-recomputed corruptions.

No candidate, X server, container, model, game, or input run occurred for this audit repair. The current `main` base observed before work was `a9352dc53c783f1501046d762bc36c34bc6ab480`.

