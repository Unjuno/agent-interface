# #4926 result — PASS_CONTROL_MAP_CLEANUP_SCOPED

Date: 2026-09-28 JST
Allocation: `temporal-resume-control-map-cleanup-20260928-01`
Frozen source revision: 02, commit `fdeca2c76e7f04385de94170f1a07a641f3c1df8`

## H/T/D/C/U

**H — hypothesis.** Correctly observing temporary-copy existence both inside and after its `TemporaryDirectory` scope will establish removal for every changed mutation copy and the unchanged positive control, without changing frozen #4511 verifier outcomes.

**T — treatment.** On local OrbStack, one source-frozen Python 3.13.5 Docker runner invocation restored the immutable source capsule, audited the retained #4447 baseline, and invoked the frozen #4511 verifier over eleven fresh, mutated copies and one unchanged positive copy. A second, separately invoked raw-only auditor read retained outputs/evidence/source read-only and ran eight effective corruption probes against copies of its result record. Docker was `--pull=never --platform linux/amd64 --network none --read-only`, 1 CPU, 1 GiB, 64 PIDs; only output and bounded `/tmp` were writable. No temporal scientific case ran.

**D — outcome.** `PASS_CONTROL_MAP_CLEANUP_SCOPED` under the frozen gates.

- Baseline verifier: exit 0; 54 rows, 48 candidate matches, 40 comparator disagreements, six corruption refusals, six recorded Docker batch receipts, `errors=[]`; manifest SHA matched the pinned value.
- All eleven byte-changing mutations were independently distinguished by changed tree hash and rejected (11/11, each verifier exit 1), including the original case_id 48 `foreign_epoch` refusal-to-OK control.
- The unchanged positive control was accepted (exit 0), remained byte/tree-identical, existed inside its temporary scope, and was absent after scope exit.
- Every mutation copy existed inside scope and was absent after scope (11/11); all 12 removals were recorded after the scope ended.
- Independent raw-only audit: `errors=[]`; 8/8 copied-result corruption probes rejected. Original evidence and source tree hashes were unchanged before/after.
- Runner invocation 1/1; separate independent auditor invocation 1/1; temporal scientific case reruns 0. No retries or post-result tuning.

## Preservation and incidents

No #4447 scientific row was executed. #4447 `HOLD_AUDIT_CONTROL_CANDIDATE_RETURN_CODE`, #4511 `HOLD_GATE_CONTROL_DENOMINATOR`, and #4534 `HOLD_POSITIVE_CONTROL_CLEANUP_RECEIPT` remain unchanged; this result does not upgrade their outcomes. The earlier rev01 preformal host source check is preserved in the Issue thread and Git history; rev02 governs the run. Prelaunch 01 is separately retained at `prelaunch/01.md`: an incorrect empty-directory size predicate stopped before Docker, with no runner/verifier invocation. Construction 01/02 separately retain the synthetic contract and source-capsule restoration checks.

## Limits

This is a same-author, deterministic, offline copied-evidence control audit. The eight controls validate the frozen auditor against specified tampering; they are not independent human review or prevalence estimates. No scientific temporal case, model, GUI, input, network service, runtime, production behavior, durability, or performance was tested. Historical predecessor fixture-byte identity and Docker kernel/glibc equivalence remain unresolved. Prior HOLDs and broader ROADMAP stay open.

## Raw identities

- `BASE_AUDIT.json` SHA-256 `096893d8e75697ed6305e4a797f6bcbbeca3dadec687e5fc3eba101a62d0e1cf`
- `CONTROL_RESULTS.json` SHA-256 `b22a016b4ce33172e4fa6e8827045708b8e7faaab935d4400601272b6e2f881b`
- `audit/AUDIT.json` SHA-256 `646230ea74d209c8af613b05a831effb61e876d3fa2d79edb154c01b50fc1bfe`
- `audit/AUDIT_CONTROLS.json` SHA-256 `cefe87397638cde451ddefed9eab41e547aa67d5c4d550456b821a051d069767`

Outer command/output/exit receipts are retained in `OUTER_RUNNER.json` and `audit/OUTER_AUDIT.json`. All source/evidence mounts were read-only. The formal outputs are additive and do not overwrite predecessor artifacts.
