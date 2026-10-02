# Independent full-payload re-audit v2

This is a separately versioned auditor-only follow-up. It does not change or
rerun the candidate, and it leaves the original `AUDIT.json` and its receipt
unchanged. Code review found that v1 checked each target mutation and reason
but did not require every other field in a case to match the frozen pristine
fixture. A collateral change to a non-target field could therefore pass v1 if
the target mutation still triggered the same first rejection.

## H / T / D / C / U

- **H:** An independent auditor that reconstructs all nine expected input
  payloads and exact decision objects will accept the immutable original raw
  bundle, while rejecting both the four existing re-sealed mutations and a
  collateral-field edit where the attacker also updates parsed rows and wire
  JSON consistently.
- **T:** Freeze a new `audit_v2.py` plus tests, bind it to the unchanged v1
  `FREEZE.json`, candidate, upstream adjudicator, `RAW.json`, and `RUN.json`.
  Read the existing candidate raw only; run no candidate or legacy auditor.
  Execute this new auditor exactly once after the preflight suite passes.
- **D:** `PASS_HOST_JSON_BOUNDARY_AUDIT_V2` iff exact canonical wire text,
  parsed rows, and full decisions match the independent reconstruction for all
  nine cases; source/raw/run/freeze identities match; and five re-sealed
  mutations reject (omitted case, duplicate case, forged decision, altered
  bound identity, and collateral payload edit).
- **C:** Host CPython 3.14.5 standard library only; no container, model, GUI,
  game, input, network, or candidate invocation. All v1 artifacts remain
  byte-identical.
- **U:** This strengthens audit integrity only; it does not change v1 candidate
  outcomes, establish a transport boundary, or add live MAP01 evidence.
