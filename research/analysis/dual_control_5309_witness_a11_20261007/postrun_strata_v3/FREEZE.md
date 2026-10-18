# A11 post-run strata V3 freeze

- Diagnostic allocation: `5309-TOPOLOGY-DEPENDENT-A11-POSTRUN-STRATA-V3`
- Source workload allocation: `5309-TOPOLOGY-DEPENDENT-A11-HOST-20261007`
- Source result package: `research/analysis/dual_control_5309_witness_a11_20261007/`
- Status before execution: frozen, not run.
- Purpose: a read-only reconstruction of descriptive strata from retained bytes. This is not a candidate/environment/formal-auditor run and cannot alter the A11 formal disposition.
- V2 disposition: provenance under review; this V3 neither validates nor retroactively repairs V2.

## H / T / D / C / U

- **H:** The retained A11 input, choices, raw rows, and oracle can be deterministically reconciled into topology-derived corrected strata, with each raw transition and completion matching the oracle and no unsupported completion.
- **T:** Load only the four frozen JSON inputs below. Recompute whether each action reaches that case's oracle witness state, classify cases as prior witness / correct prediction with an affordable preserving action / correct prediction with preservation over budget / correct prediction with no preserving action / misspecified prediction, and independently reconcile both policy rows for every case. Execute the frozen V3 audit script once, host CPython standard library only. Candidate/environment/formal auditor invocations: 0; retries: 0. No container is used because this is a read-only parser and the contemporaneous A09 Docker STOP makes engine repair or image mutation out of scope.
- **D:** `PASS_RETAINED_STRATA_RECONSTRUCTION` only if exactly 132 cases and 264 unique arm rows are present, all transitions and witness decisions reconstruct exactly, errors and unsupported completions are empty, and the output identifies V3 as `allocation`, A11 as `source_allocation`, and `formal_a11_verdict_changed=false`. Any mismatch is retained as FAIL/STOP; no retry.
- **C:** This is post-hoc descriptive reclassification of an authored deterministic fixture, not a new preregistered hypothesis test, independent external audit, or evidence about natural GUI behavior. The classification logic is based on the retained oracle and does not validate the oracle's real-world relevance.
- **U:** Does not establish topology transfer, real application effects, safety, calibrated costs, timing, user benefit, or product performance. The formal A11 verdict remains `FAIL_AUDIT_MISSPECIFIED_STRATUM_GATE` regardless of this diagnostic.

## Frozen source hashes

```text
7ecbdab67ee0d36c5e95c03c2a2d3fe6b553823d418c128b5ff4f954f743dc35  postrun_strata_v3/audit.py
c07166f9e934a891eb47fcf8bd4bf115c56f9ad49b2de11b2966dca7366f57cf  candidate-input.json
d1be192e7e30aa533a089f66de04b77eb63eef77462a4aaa411cc991a8c3793b  candidate-choices.json
06e86d08d489809845649b28e2a36b2c212f690cb4a20b461b4172f639ea7545  candidate-raw.json
e4eef4add33d7e54a86ab1e9697cd93c255de3fbae9a595231ff066bfe5d08c1  oracle.json
```

## One permitted command

From the repository root, after committing this freeze and confirming the output files do not exist:

```sh
python3 -B research/analysis/dual_control_5309_witness_a11_20261007/postrun_strata_v3/audit.py \
  research/analysis/dual_control_5309_witness_a11_20261007/candidate-input.json \
  research/analysis/dual_control_5309_witness_a11_20261007/candidate-choices.json \
  research/analysis/dual_control_5309_witness_a11_20261007/candidate-raw.json \
  research/analysis/dual_control_5309_witness_a11_20261007/oracle.json \
  research/analysis/dual_control_5309_witness_a11_20261007/postrun_strata_v3/result.json \
  > research/analysis/dual_control_5309_witness_a11_20261007/postrun_strata_v3/stdout.json
```

Invocation count is exactly one. Do not rerun V3 or edit the frozen script/inputs after execution. Preserve any nonzero exit or unexpected output as the terminal V3 outcome.
