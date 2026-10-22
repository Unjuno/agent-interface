# Scorer endpoint readback type guard — A02

Status: `FAIL_OPEN_ENDPOINT_TYPE` (candidate) / `PASS` (independent audit).

## H/T/D/C/U

- **H:** The pinned #7685 candidate accepts non-integer post-snapshot episode-time values when equality aliases them to the acknowledged integer tic.
- **T:** Execute the exact pinned candidate with valid integer control (10→11/read 11), float alias (10→11/read 11.0), and Boolean alias (0→1/read True). The stub implements the candidate's configured-variable-order API. Audit the saved rows and source pin independently without re-executing the candidate.
- **D:** FAIL_OPEN_ENDPOINT_TYPE if the integer control qualifies and either alias qualifies; PASS_FAIL_CLOSED only if control qualifies and both aliases fail closed without values; HOLD if control fails, source differs, or audit errors.
- **C:** Real ViZDoom may always return integers; this checks the candidate's defensive type contract, not a real API violation.
- **U:** Deterministic stub test of a non-integrated PR candidate. No game, scorer, X server, model, GUI, input, task effect, or recovery behavior is measured.

## Provenance

Main at freeze: `d12d451ae5e7661adc3b261403196b1af72e2851`. Candidate PR head: `5b4a563b5c3f6a70a063a98c7281a8bd6ce71eb0`; candidate source SHA-256: `c48c1a734ae32505d7adf000028e618b2d0cfe73a4aa969892b8aada6a6407f5`. Candidate harness and independent auditor are hash-pinned in `FREEZE.json`. No retry is authorized.

## Result

One candidate run, exit 0. The valid integer control returned `REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING` and retained the snapshot values. The float alias (`tic_after=11`, readback `11.0`) and Boolean alias (`tic_after=1`, readback `True`) returned the same pending status and also retained values. The independent auditor passed all seven checks with zero errors. Candidate stdout and per-case rows are retained in `RESULT.json`.

This confirms a deterministic equality/type fail-open in the frozen candidate source. It does not show that the real API emits floats or booleans, or that the candidate is merged, integrated, or exercised against a game. A corrective implementation should require exact `int` type for the post-read tic before comparing and add float/Boolean regressions.
