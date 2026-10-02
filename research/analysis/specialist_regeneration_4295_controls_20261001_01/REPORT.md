# #4295 audit-control-only successor result

## Result

**PASS_AUDIT_CONTROLS_SUPPLEMENTAL.** The correctly invoked frozen control
harness rejected all 12/12 preregistered mutations. Its exit status was 0;
each child audit exited 1. A separate `jq -e` structural check confirmed 12
entries, all rejected, with child exit 1.

This does not relabel the predecessor allocation's
`STOP_PROTOCOL_DEVIATION`. It repairs only the missing mutation-control
evidence for the exact retained candidate raw; no candidate or formal row was
rerun. The control-successor result alone does not establish the Issue
hypothesis.

## H / T / D / C / U

- **H:** The frozen raw-only auditor rejects at least 10/12 frozen mutations
  when the control harness receives the actual auditor script path.
- **T:** One control-only invocation used the preserved candidate raw and
  unchanged frozen `controls.py` / `audit.py` source. Candidate invocations=0.
- **D:** `PASS_AUDIT_CONTROLS_SUPPLEMENTAL` requires exit 0, all 12 controls
  present, and at least 10 rejected. Observed 12/12 rejected; all child audit
  exits were 1.
- **C:** This is only the frozen 12-mutation set over one retained synthetic
  raw. It is same-author process separation, not external review.
- **U:** It says nothing about learned specialists, generalization, latency,
  energy, task value, GUI behavior, or production readiness.

## Frozen inputs and command

- Raw SHA-256:
  `8fe7767b456cc5ca70285b426c492675952c3247f55400d71233aa9780412d3e`.
- Clean audit SHA-256:
  `0dd886dd70f6e86622ba74a6aa98b4d3faf94b2e394816c6a41eb51316869b34`.
- `controls.py` SHA-256:
  `e23d7af971a4f25acdbce379cf7161db4c4ebbe969f0a9aaa6efaf9202e545f0`.
- `audit.py` SHA-256:
  `d4d70a22b26e9c32f474417d7fc6c4e34ad776e7e34c65ab176e680bf8f51055`.
- Output SHA-256:
  `6fc1aa0defea269232722b8cb5d5ed6e7b48659c66da5d69c946dbda09804487`.
- Command (exit 0):

```text
python3 -B research/analysis/specialist_regeneration_4284_preformal_preserved_4295_v1/source/controls.py research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/FORMAL_RAW.json research/analysis/specialist_regeneration_4284_preformal_preserved_4295_v1/source/audit.py research/analysis/specialist_regeneration_4295_controls_20261001_01/CONTROL_RESULTS.json
```

No retry, replacement, or candidate invocation occurred. The first allocation's
failed `CONTROLS.json` remains unchanged beside its STOP record.
