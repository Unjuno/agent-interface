# #6155 T0f — repeated-look interval and coefficient-leakage audit

**Disposition: `PASS_METHOD_SCOPED`.** The finite synthetic experiment shows that the preregistered repeatedly inspected ordinary intervals cross a positive-effect boundary in 14.36% of null streams, while the bounded Hoeffding confidence sequence crossed in 0/10,000. On the planted `delta=0.15` stratum, the fixed-beta sequence detected 10,000/10,000 by the maximum horizon; the deliberately same-row-fitted coefficient erased the effect in all 10,000 streams. Independent raw-only replay matched every row and rejected all four row-corruption controls.

## Frozen question and design

The study tests only the additive T0f question in [Issue #6155](https://github.com/Unjuno/agent-interface/issues/6155): whether repeated ordinary fixed-sample intervals can over-stop under a planted null and whether fitting a control-variate coefficient from the same current high-fidelity row can erase a true target effect. It does not revise or pool the distinct #6155 v1–v4 or route-contrast T0e results.

Each stratum contains 10,000 independent streams of 1,024 observations. For each row, independent `X` and `epsilon` are equiprobable `-0.25` or `+0.25`; `Y=delta+X+epsilon`; the target is `E[Y]=delta`, and `E[X]=0`. The valid arm uses prospectively fixed `beta=1`, so `Z=Y-X=delta+epsilon` lies within `[-0.5,+0.5]`. Looks are fixed at 8, 16, 32, 64, 128, 256, 512 and 1,024. The naive rule repeatedly checks an ordinary two-sided 95% normal interval. The confidence sequence uses `alpha_t=0.05/(t(t+1))` at every integer time, with the preregistered Hoeffding bound; the inspected looks are a subset. The deliberately invalid control fits `beta_i=Y_i/X_i` on that same row; it is diagnostic only.

Full H/T/D/C/U, gates, seed, hashes and source/main identities are in [PROTOCOL.md](PROTOCOL.md), [fixture.json](fixture.json) and [FREEZE.json](FREEZE.json).

## Result

| Stratum | Repeated ordinary 95% interval | Fixed-beta Hoeffding CS | Same-row leakage control |
|---|---:|---:|---:|
| Null (`delta=0`) | 1,436/10,000 stopped (14.36%; median stop 32) | 0/10,000 stopped | 0/10,000 stops; max absolute final estimate 0 |
| Positive (`delta=0.15`) | 10,000/10,000 stopped (median 16) | 10,000/10,000 detected (median 512) | 0/10,000 detected; max absolute final estimate 0 |

The auditor reconstructed 20,000/20,000 rows, reported `errors=[]`, and rejected 4/4 frozen altered-row controls. Candidate exit 0; independent auditor exit 0; each invoked exactly once; retries 0. The preregistered numerical decision gates all passed.

## Interpretation limits

This demonstrates the stated behavior only for the frozen bounded i.i.d. synthetic process and its filtration. The fixed coefficient is known and fixed prospectively, not estimated from an actual pilot; the same-row coefficient arm is intentionally pathological. The result does not validate adaptive stopping for arbitrary GUI/model outcomes, account for real task dependence, nonstationarity, censoring or missingness, estimate real costs, or establish any safety/correctness benefit. Cheap `X` output cannot replace high-fidelity effect scoring or a hard safety gate. No GPU, container, WSLc, model/provider, network, GUI or input was used.

## Reproduction

Run candidate once and only then run the raw-only auditor once:

```powershell
python research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/candidate.py research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/fixture.json research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/raw/candidate.jsonl
python research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/audit.py research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/fixture.json research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/raw/candidate.jsonl research/analysis/multifidelity_control_variate_6155_t0_v5_anytime/raw/audit.json
```

The exact 20,000-row raw stream is retained losslessly as `raw/candidate.jsonl.gz.base64`; decode base64, gunzip, then verify against [SHA256SUMS](SHA256SUMS). `RUN_RECORD.json` records commands, exit codes, durations and artifact hashes.

