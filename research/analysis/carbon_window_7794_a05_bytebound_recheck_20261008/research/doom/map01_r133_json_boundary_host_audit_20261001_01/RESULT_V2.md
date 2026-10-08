# MAP01 JSON boundary audit correction — retained v2/v3 supplement

This supplement preserves `RESULT.md`, the original candidate raw, the v1
audit receipt, and the v2 failed-attempt receipt unchanged. It narrows the
original claim in light of independent auditor review.

## H / T / D / C / U

- **H:** v3 can fully reconstruct all nine canonical JSON payloads and exact
  adjudicator decisions from the immutable candidate raw, reproduce the v1
  false-accept counterexample, and reject five re-sealed mutations.
- **T:** Ran v3 preflight tests on retained evidence (2 passed), then invoked
  the v3 audit entrypoint exactly once. Candidate, v1 auditor and v2 auditor
  were not rerun. The v2 failure and v1 receipt remain as historical evidence.
- **D:** `PASS_HOST_JSON_BOUNDARY_AUDIT_V3`; 9 cases, `errors=[]`,
  `source_errors=[]`, and 5/5 mutations rejected. The v1 false accept was
  reproduced. v2 remains `STOP_AUDITOR_IMPLEMENTATION_ERROR` (`NameError` in
  result construction), not a passing audit.
- **C:** Auditor-only host analysis, CPython standard library, immutable
  synthetic raw. No Docker/OrbStack, live game, input, network, or effect.
- **U:** This repairs only the evidentiary audit of synthetic JSON-boundary
  construction. It is not a formal container run, live MAP01 threat/safety/
  efficacy/latency result, and does not close Issue #59.

## Evidence chain

- Candidate raw SHA-256: `8d78e5fc8f5df2aea7aa2f7e33caf35002477d0f83ba983909d91c91c8f45c7c`
- v1 auditor source SHA-256: `97423a9566d347f9300da94dd67eed7ca856857ae3d94c273c8a433ef7c524c0`
- v1 false accept: a `pair_id_bool` payload was consistently modified in both
  parsed rows and `wire_json`, including unrelated `health_loss`; v1 still
  returned no errors because it checked only the target malformed field.
- v2 attempt SHA and exact implementation stop are retained in
  `AUDIT_V2_ATTEMPT.json`.
- v3 exact source pins are in `FREEZE_V3.json`; outcome is
  `results/construction-01/AUDIT_V3.json`.

Do not rerun the candidate or earlier auditors to reproduce this allocation.
The unresolved main research gate remains a bounded, properly coordinated
live threat-control experiment under Issue #59.
