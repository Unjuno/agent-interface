# Issue #5440 — T1 formal result

Disposition: **PASS_T1_SYNTHETIC_SENSITIVITY_GATE**. This supports the preregistered mechanism only in the authored synthetic model; it is not a causal estimate, production safety result, or real action-correctness finding.

- Hosted run: [36717250281](https://github.com/Unjuno/agent-interface/actions/runs/36717250281), source commit `32db1c3fdc6e50dd6d64c3d6886e503c94144fd6`, frozen base `ffb0d43b5f0408011a3f70223da43d4aa3f27fe4`.
- Runtime: GitHub-hosted `ubuntu-24.04`; `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `linux/amd64`; `--network none`.
- Candidate was invoked exactly once. The container step, preflight, candidate and in-container independent audit all succeeded.
- 16/16 candidate rows matched the independent exhaustive-vertex oracle (128 vertices). Four of four corruption controls were rejected.
- 4/16 claims were sensitivity-abstentions (25%). At the same abstention budget, the nominal-margin-only comparator left 2 non-positive worst-case claims admitted; the sensitivity gate left 0.
- Input SHA-256: `02ba32c8f1a4c8ab3d65e7fa138f459602a22a8ab2224859d9b916315a14f20e`; candidate: `ec6adc9966d439a247f30ccb50b42f1185f7522393e60f2b65daabaf36e1a680`; raw: `73fd273ee89a3c2cd8741622831aeee15184068fcefdcaaaee00c7ce2b733708`; audit: `a5ced8ce7588d88c410dc9434f9bc059cbcdab9d4e7e83b9fbae29b44286557c`; artifact archive: `62977afc051311bd4f0325ee00ce15b92b65753bed05f0e45400f0814be5f104`.
- The Actions run is nevertheless **FAILURE_POSTRUN_RECEIPT_STOP**: after writing the execution-status file, the runner could not append its digest to the container-owned `SHA256SUMS` (permission denied). The raw/audit artifact was uploaded. All 10 entries in that original manifest were independently matched to the artifact and exact GitHub source bytes. A separate status-digest sidecar is supplied; no candidate retry is permitted.

The eight earlier workflow-file failures had zero jobs, zero artifacts and zero candidate invocations; they are preserved in `workflow-activation-stops.json`. The post-run receipt failure is separate in `postrun-delivery-stop.json`.

## H / T / D / C / U

- **H:** Supported within this synthetic matched set: under the declared latent-cause model, the sensitivity gate separated robust from sensitive nominal claims while the equal-budget nominal-margin comparator admitted two non-positive worst cases.
- **T:** Frozen 16 exact-rational evidence graphs, 8 matched pairs, 3 shared/private causes per graph, closed-form candidate vs exhaustive vertex oracle.
- **D:** PASS: 16/16 rows matched; 4/16 sensitivity abstentions; 0 residual unsafe sensitivity admissions vs 2 for margin-only; all 4 mutations rejected; source/raw manifest passed.
- **C:** Authored deterministic monotone linear effects, attested synthetic nodes, rectangular uncertainty bounds. No statistical or causal estimation.
- **U:** Real latent bounds/dependencies, observer truth, missing evidence, action-class losses, calibrated abstention budgets and production utility remain unknown.

Do not infer broad causal validity, calibration, deployment safety, or automatic actuation authority. The audit-only workflow must pass on the committed result branch before delivery is considered complete.
