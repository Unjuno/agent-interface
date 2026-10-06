# Boundary blame T0 — Issue #5313

## Disposition

`PASS_BOUNDARY_BLAME_SCOPED` for allocation `BOUNDARY-BLAME-5313-T0-20261006-01`.

Finite synthetic diagnostic/repair-routing evidence only. No live GUI fault localization, maliciousness/personnel responsibility, security attribution, production safety, latency/token benefit, or task-utility claim.

## H / T / D / C / U

**H.** Direct typed boundary evidence localizes the declared single faults; paired direct faults remain `MULTI_CAUSE`; incomplete/externally ambiguous evidence remains `UNLOCALIZED`. Repair routing should reduce wrong repair and repeat failure without changing admission or authority decisions.

**T.** Twelve frozen cases over seven observed boundaries: clean; six singles; three pairs; one missing-evidence case; one externally ambiguous failure. Candidate received only public boundary records. Hidden fault truth was available only to a separately structured auditor. Candidate, auditor and copied-result controls were invoked once each after complete source/freeze publication and Git blob readback.

**D.** Require exact singles, no pair collapse, exact required UNLOCALIZED cases, zero unsafe admission/authority differences, strictly fewer candidate wrong repairs/repeat failures, audit errors=[], and >=8 effective corruption rejections.

**C.** The authored fixture makes direct fault evidence unusually clean; a simpler causal trace may produce the same routing benefit.

**U.** Complete finite evidence only. Hidden/correlated faults beyond the authored pairs, live receipt schemas, environment nondeterminism, model/GUI/task effect and external validity remain open. Same-author separate implementation is not independent human review.

## First formal outcome

- Candidate: 12/12 rows, scientific process exit 0, retries 0.
- Auditor: `PASS_BOUNDARY_BLAME_SCOPED`, 49 checks, 0 errors, exit 0.
- Corruption controls: 8/8 rejected, exit 0.
- Single faults exact: 6/6.
- Paired faults preserved as `MULTI_CAUSE`: 3/3.
- Required `UNLOCALIZED`: 2/2.
- Unsafe admissions: 0.
- Authority-decision differences: 0.
- Baseline wrong repair / repeat failure: 10 / 10.
- Candidate wrong repair / repeat failure: 0 / 0.

The clean control is the only `ALLOW` / `authority_granted=true` row. All failure rows remain `BLOCK` / false. Blame never expands authority.

## Preserved execution anomaly

The candidate Python process completed exit 0 and wrote the 12-row result plus its receipt. The enclosing execution wrapper then returned status 1 with `TERM environment variable not set.` No candidate retry occurred. Auditor and controls consumed the retained first candidate output and both completed successfully. This is retained as `formal/outer_harness_stop.json`; it does not overwrite the scientific process exit.

## Source / integrity

Base main: `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028`.
Pre-execution Git readback matched local blobs for `FREEZE.json`, `PREEXECUTION.md`, and the complete source capsule. Frozen source XZ SHA-256: `641673195771c78a51c8767f35b900afe211541a7a6bfa9485c165b7870ffe53`.

Formal raw SHA-256 values are in the formal capsule. Eight copied-result mutations reject wrong blame, pair collapse, unsupported localization, authority flip, wrong/incomplete repair, unsafe ambiguous admission, and row deletion.

## Environment

Provided Linux x86_64 execution container, CPython 3.13.5, standard library only. Not claimed as WSLc/OrbStack/Docker image-attested replication. No GUI/model/provider/user data/network experiment/OS input.

## Integration boundary

Keep diagnostic cause attribution separate from authority; retain multi-cause and unknown outcomes instead of forcing one culprit; route repair only where the evidence supports it. A distinct successor should replay real retained receipt schemas with an independently specified fault/evidence oracle before any runtime promotion.
