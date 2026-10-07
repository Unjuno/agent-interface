# Issue #5309 pairwise identifiability A01 — invalid audit / STOP

## Disposition

`FAIL_AUDIT_CONTRACT_INVALID` (no scientific PASS/FAIL inference). The frozen candidate completed once in OrbStack with exit 0. The frozen independent auditor also completed once with exit 0 and printed `PASS_METHOD_SCOPED`, but raw inspection and contract challenge show the candidate fixture and auditor both violate the pre-registered test. Preserve both outputs unchanged; do not rerun this allocation.

## H / T / D / C / U

- **H:** A one-step information score/repeated benign action may leave safety-relevant hidden-state pairs indistinguishable; a bounded pairwise oracle must return `UNKNOWN/YIELD` when no admissible separator fits before expiry.
- **T:** Four finite scenarios: separator available, no separator, expiry before separator, and one-step null. Compare one-step selection, repeated same-action path and independent finite pair oracle. Record proposal/admission/execution/observation separately and authority as false.
- **D:** The pre-registered gate required all incompatible-commit pairs, exact pair-history discrimination, correct expiry/admissibility handling, null acceptance, refused-observation censoring, no authority promotion, and an independently represented oracle. Any missed/incorrect pair or contract error fails the allocation.
- **C:** Existing explicit safe probes and freshness/risk gates may suffice; the finite mechanism may be unnecessary.
- **U:** Even a valid finite method result would not establish GUI transfer, nonstationary state, global impossibility, live safety, or utility.

## Executed run

- Checkout/HEAD: `research/8135-persistent-counterparty-t1-prep-main2c1c90-20261005`, `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Image: `node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80` (already cached; no pull/build).
- Candidate: one named OrbStack invocation, network `none`, read-only rootfs, source read-only bind, CPU 1, memory/swap 256 MiB, pids 16; exit 0, stderr empty.
- Independent auditor: one separate named OrbStack invocation, network `none`, read-only rootfs/source, CPU 1, memory/swap 128 MiB, pids 16; exit 0, stderr empty; emitted PASS, but the PASS is invalid.
- Retries: 0. No GitHub Actions, model, GUI, network or external action.

## Why the PASS is invalid

1. Candidate transition keys `nosep_a`/`nosep_b` are created through a whitespace-containing temporary key and then reassigned. Its observation function therefore returns no transition for those cases. Candidate output nevertheless reports information score 1, no observed repeated history, and `repeated_branch_preserves_pair_alias=false`, rather than the registered no-separator prediction (two routine observations and alias preserved).
2. In the expiry case, the candidate marks expiry after the first step, yet its purported one-step action is also at step zero and is emitted as admitted with null observation. The candidate does not model the required path/separation decision.
3. The auditor’s search tests whether the entire left/right history arrays equal their own reversal. It does not compare the two histories (`histories[0]` vs `histories[1]`). Thus it can report `separated=true` even for equal histories. It also does not verify the candidate's `one_step_information_score`, repeated-history alias claim, expiry boundary, or exact action-event correspondence. This was confirmed by auditor output accepting the frozen raw despite items 1–2.
4. The candidate fixture and auditor fixture disagree on no-separator/expiry observation semantics and use different pair IDs. Therefore the independent oracle did not reconstruct the frozen candidate model.

Because the scorer/auditor gate is invalid, `PASS_METHOD_SCOPED` is rejected. The raw does demonstrate implementation defects, not evidence for or against H.

## Post-run preservation validation

- Successor construction regression contract (pairwise equality negative/positive controls, expiry boundary, and rejection of the immutable A01 no-separator raw): PASS.
- `node --check candidate.mjs`: PASS; `node --check auditor.mjs`: PASS.
- SHA-256 manifest verification: PASS after the test/report files were frozen.
- Candidate/auditor formal re-executions after the A01 runs: 0. The regression test reads the retained raw; it does not rerun the A01 candidate or auditor.
- Full repository CI, semantic successor candidate, and repaired independent audit are not claimed.

## Preserved files

- `PRE_REGISTRATION.md`, `candidate.mjs`, `auditor.mjs`, `test_construction.mjs`
- `candidate-raw.json`, `candidate-stderr.txt`, `candidate-container-config.json`, `candidate-container-result.txt`
- `audit-attempt-1.stdout.json`, `audit-attempt-1.stderr.txt`, `audit-container.stdout.json`, `audit-container.stderr.txt`
- `SHA256SUMS.txt`

Any correction requires a separate successor allocation with new source freeze, pair-history oracle controls (including equal-history negative control), and fresh immutable path. Do not alter or replay A01.
