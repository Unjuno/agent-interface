# Independent full-payload re-audit v3

This is a separately frozen auditor-only correction after two retained review
findings: v1 accepted a re-sealed collateral-field edit that preserved its
target mutation, and v2's first execution stopped in result construction with
`NameError`. Both historical auditor records are preserved. Candidate, raw,
run receipt, v1 audit and v2 audit source/freeze are unchanged.

## H / T / D / C / U

- **H:** A fully exercised v3 audit entrypoint accepts the exact immutable
  candidate raw after reconstructing all nine complete canonical JSON payloads
  and full decision objects, and rejects five re-sealed copied-evidence
  mutations including collateral-field edits.
- **T:** Pin this plan, v3 CLI/orchestrator, its preflight tests, the v2 pure
  independent payload checker, original freeze/candidate/upstream source, raw,
  run, v1 audit, and recorded v2 failed-attempt receipt. Preflight tests exercise
  the full v3 orchestration on retained bytes without writing a new audit
  result. Then run v3 exactly once against the immutable raw and save a new
  `AUDIT_V3.json`. No candidate or earlier auditor is rerun.
- **D:** `PASS_HOST_JSON_BOUNDARY_AUDIT_V3` iff every pinned identity matches,
  all nine complete canonical wire payloads/parsed rows/decisions match the
  independent reconstruction, the v1 false-accept counterexample is rejected,
  and five re-sealed mutations reject. Any source/raw/decision/audit error is
  `STOP_HOST_AUDIT_V3`.
- **C:** CPython 3.14.5 standard library only; auditor-only work on retained
  synthetic data. No Docker/OrbStack, model, GUI, game, input, network, or
  candidate invocation.
- **U:** This is an audit-integrity correction only. It does not change the
  candidate's output or substantiate live MAP01, transport, safety, efficacy,
  latency, or runtime claims.

The pre-freeze v3 test suite must exercise `run_audit()` end-to-end and the
collateral mutation after both `wire_json` and parsed rows are consistently
re-serialized. If any test fails, do not run the frozen v3 auditor.
