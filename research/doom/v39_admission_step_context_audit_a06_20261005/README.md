# V39 admission step-context strict raw audit — A06

This is an audit-only follow-up to Issue #59 and the saved-result package in PR #7692 (A05). It does not edit or replace A05 or its reported result.

## H / T / D / C / U

**H.** Independently reconstructing every published row and summary field from the pinned `runtime/events.jsonl` will detect derived-output corruption that a structural audit can miss.

**T.** The frozen plan called for one successful strict-auditor invocation in a network-disabled WSLc CPU container, with zero retries. Read the exact A05 frozen input snapshot from PR #7692 head `0cc79dc4614b97751949960842013bd954c99dd7`: `FREEZE.json`, `RESULT.json`, `analyze.py`, `audit.py`, and `FILES.sha256.json`. Read the copied raw event stream pinned by that freeze and verify its SHA-256, independently reconstruct all 39 admission rows, all receipt projections, counts, timing summaries, scope labels, and source metadata, then compare the complete output object. Verify every copied A05 input against `FILES.sha256.json` and apply 15 result-only mutations in memory; do not rerun the candidate or change the A05 package. Actual deviations are retained and explained in `RUN.json`.

**D.** `PASS_SAVED_RESULT_AUDIT_SCOPED` only if the frozen raw bytes match, the independently reconstructed complete output equals the retained A05 result, and all 15 distinct derived-field mutations are rejected. Any un-rejected mutation or reconstruction mismatch is `FAIL_AUDIT_COVERAGE`; source/provenance or container failure before evaluation is `STOP_INFRA`. No result may be interpreted as per-key release or live-control evidence.

**C.** The original audit may be intentionally scoped to selected structural fields; stronger reconstruction increases maintenance cost and can inherit the same source interpretation if not independently implemented.

**U.** One saved event stream and one synthetic audit-control matrix. This does not rerun the V39 candidate, validate live per-key up/release timing, prove physical input state, task usefulness, bounded recovery, matched benefit, or MAP01 completion. No GPU, model, GUI, input, or game allocation.

## Frozen inputs

The five A05 input files are copied byte-for-byte under `input_a05/`. Their origin is PR #7692 head `0cc79dc4614b97751949960842013bd954c99dd7`. The raw source remains pinned to commit `c99d93a2c81945f0946173e48247bdd49e32a02a`; no candidate invocation is part of this audit.

## Execution

The raw bytes are retained at `input_raw/events.jsonl`; the five A05 inputs are byte-for-byte copies under `input_a05/`. The freeze, source/file digests, WSLc command, container inspect/log receipts, independent audit outputs, mutation results, stopped-attempt logs, and final hashes are recorded in `FREEZE.json`, `RUN.json`, `formal_01/`, `formal_02/`, and `SHA256SUMS`. `formal_01/AUDIT_INITIAL_SUPERSEDED.json` preserves the first passing reconstruction, but its input-hash boolean was vacuously true because the auditor did not read the input manifest. The corrected auditor now checks all five A05 files against their frozen hashes and checks source provenance; only `formal_02/AUDIT.json` is the final result. The first container attempt stopped because the minimal image has no `git` executable; the corrected run reads the pinned raw file directly. WSLc warned that kernel swap/cgroup accounting is unavailable, so the requested 512 MiB memory limit is not claimed as enforced. Two additional container executions beyond the single planned invocation are recorded as deviations in `RUN.json`.
