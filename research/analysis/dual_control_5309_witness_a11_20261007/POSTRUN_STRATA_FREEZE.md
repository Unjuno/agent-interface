# Post-run A11 strata audit freeze

Diagnostic allocation: `5309-TOPOLOGY-DEPENDENT-A11-POSTRUN-STRATA-V2`. Source workload allocation: `5309-TOPOLOGY-DEPENDENT-A11-HOST-20261007`. The result JSON must retain these as distinct `allocation` and `source_allocation` fields. This read-only analysis was defined after the formal A11 outcome and cannot alter that outcome. It reads only the retained input, choices, raw rows, and oracle; it does not invoke any formal stage.

Frozen source hash:

```text
634ac61ca2e718c7e9c859ab9b88b5ca461ddb02381b6ada8bc4e941f3aa1d22  audit_retained_strata_v2.py
```

Frozen retained-input hashes:

```text
c07166f9e934a891eb47fcf8bd4bf115c56f9ad49b2de11b2966dca7366f57cf  candidate-input.json
d1be192e7e30aa533a089f66de04b77eb63eef77462a4aaa411cc991a8c3793b  candidate-choices.json
06e86d08d489809845649b28e2a36b2c212f690cb4a20b461b4172f639ea7545  candidate-raw.json
e4eef4add33d7e54a86ab1e9697cd93c255de3fbae9a595231ff066bfe5d08c1  oracle.json
```

Single command, run once after this freeze:

```bash
python3 research/analysis/dual_control_5309_witness_a11_20261007/audit_retained_strata_v2.py \
  research/analysis/dual_control_5309_witness_a11_20261007/candidate-input.json \
  research/analysis/dual_control_5309_witness_a11_20261007/candidate-choices.json \
  research/analysis/dual_control_5309_witness_a11_20261007/candidate-raw.json \
  research/analysis/dual_control_5309_witness_a11_20261007/oracle.json \
  research/analysis/dual_control_5309_witness_a11_20261007/audit_retained_strata_v2.json
```
