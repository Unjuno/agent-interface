# Issue #5776 T0 — recovery-rate sentinel finite simulation

Status: host-only construction/precheck retained; formal Docker candidate/auditor were **not run** because current OrbStack shared daemon contains four unresolved `Created` containers and this session has no assigned isolated guest. Base main: `4bf4cb04eade179be9f5a25b130ebe53ea3a71b7`.

## H / T / D / C / U

- **H:** In a declared finite system family with a gradual loss of restoring capacity, the recovery-time sentinel can warn before service loss at a fixed held-out false-alarm ceiling; an abrupt-threshold control should not produce the same gradual-warning pattern.
- **T:** Generate a complete prospective synthetic episode population across four mechanisms (gradual slowing, abrupt breaker, stable null, and load drift), with matched reversible disturbances, calibration/test episode IDs fixed independently of outcomes, exact return-to-envelope endpoints, service-loss labels, and frozen recovery-time statistic/threshold. Candidate emits every episode including recoveries and non-events. A separately implemented auditor reconstructs all episodes/statistics and tests corruption controls.
- **D:** `PASS_METHOD_SCOPED` only if all episodes are present and independently reconstructed; on held-out gradual episodes the predeclared sentinel reaches sensitivity >= 0.75 with false-alarm rate <= 0.10 on eligible no-loss opportunities; the abrupt control does not meet the gradual-warning criterion; stable-null and load-drift negative controls remain below the same false-alarm ceiling; missing/ambiguous return endpoints are UNKNOWN and excluded from neither denominators nor counts silently. Otherwise retain exact `FAIL_METHOD`, `HOLD`, or `STOP`. Candidate prechecks predict only 5/20 gradual warnings (0.25) at the frozen calibration threshold 3.5, so a method FAIL is expected; the threshold or gate will not be changed after this prediction.
- **C:** The simulator's chosen restoring-capacity dynamics may make the answer tautological; queue level or direct margin may be a stronger sentinel; real interfaces may fail abruptly without critical slowing; disturbance probing may itself change state.
- **U:** This is deterministic synthetic-method evidence only. No measured interface traces, calibrated incident prevalence, production prediction, live task, safety-rate, causal or ecological-to-software transfer claim.

## Frozen synthetic model and analysis

Four mechanisms, each with 40 episodes and 8 fixed disturbance opportunities per episode (1,280 total opportunities): gradual capacity decline, abrupt breaker, stable null, and gradual exogenous load drift. Episode IDs 0–19 per mechanism are calibration; 20–39 are held out. Each episode has a deterministic, pre-outcome phase offset `episode_id mod 4`, so episode-level variation is present in both partitions. Operating margin is integer capacity minus integer demand, initialized at 8. A matched unit disturbance is applied at each opportunity and relaxation proceeds in discrete ticks. Recovery time is the number of ticks until the margin returns to its pre-disturbance envelope; service loss is a separate boundary crossing, never inferred from recovery time. The candidate statistic is the within-episode median recovery time over the last four opportunities; the sole threshold is frozen from calibration gradual episodes as the nearest-rank 75th percentile, and a test episode warns iff its statistic is strictly above that threshold. Denominator is all held-out episodes with the frozen eight opportunities; sentinel missingness is a failure/UNKNOWN, never dropped.

The mechanism controls test whether this exact sentinel detects gradual slowing without simply firing on every disturbance, including abrupt breaker and stable/load-drift controls. This toy model cannot test whether its assumed dynamics map to Agent Interface.

## Execution contract

- One candidate invocation, then one independent raw-only auditor invocation iff candidate exits 0.
- Frozen OCI image `python:3.12-slim@sha256:950206c37262dd86c55659797f6ee418fee30535072f65a82ed470d985f5cda5`, platform `linux/arm64/v8`; standard library only; `--network none`, 1 CPU, 256 MiB, 64 PIDs; read-only source and fresh output directory.
- Freeze every source and fixture hash before the candidate. Raw output includes complete episode and opportunity rows, allocation identity, source hashes and candidate invocation count.
- Six mutation controls: dropped no-loss episode, dropped failed episode, altered disturbance schedule, forged test threshold, missing-return recoded as success, and duplicated episode.
- No GUI, model, GPU, task input, external effect, or live perturbation.

## Host construction disposition

Host-only precheck rebuilt the complete 160-episode / 1,280-opportunity table and an independent raw-only oracle reconstruction. Frozen calibration threshold is 3.5; held-out gradual warning sensitivity is 5/20 = 0.25, below the frozen 0.75 gate. Stable-null and load-drift false alarms are 0/20 each. All 20 abrupt-breaker held-out episodes contain UNKNOWN return endpoints and remain explicitly UNKNOWN; they are not scored as negatives. The method disposition is therefore `FAIL_METHOD` on the preregistered gradual-sensitivity gate, not PASS. The raw-only oracle reports only that same gate error, and rejects all six mutations.

This is host-only construction evidence, not the planned Docker experiment. Formal Docker candidate/auditor counts remain 0/0. The method finding is useful as a falsification of this frozen synthetic detector configuration only; no retuning or retry is authorized under this allocation. A materially different threshold/model would require a new successor fixture and allocation.

## Host evidence receipt (Docker STOP)

Docker gate at 2026-10-01 04:41 UTC: context `orbstack`, server `29.4.0 linux/aarch64`. Read-only `docker ps -a --filter status=created` returned four unresolved objects: `dd009c5eb28f frosty_solomon`, `2c75cfe9989c issue4466-formal-stage-01-20260926`, `82b9804f63db issue4466-image-layer-20260926`, and `5544451d0230 issue4466-xwd-donor-20260926`. No isolated-machine CLI/API is available in this task. Disposition: `STOP_RESOURCE_COORDINATION_BEFORE_DOCKER`; Docker candidate=0, Docker auditor=0, no containers created/started/inspected/changed. The following host-only evidence is separate and cannot satisfy the Docker gate.

Host command: `python -B -m unittest discover -s research/analysis/recovery_rate_5776_t0_v1 -p 'test_*.py' -v` — 3/3 PASS. The suite exercises the frozen full-population construction, independently reconstructed `FAIL_METHOD`, and six mutation rejections. `python -B -m py_compile ...` and `git diff --cached --check` pass; the repository analysis-index check could not be run because sparse checkout excludes `research/analysis/check_index.py` (the local checkout contains only the additive target path). No generated `raw.json` or audit result is represented as a formal Docker artifact.

SHA-256: `fixture.json` `f19d35fc38b5fc48ad407f6d13fa10a18fa2f2b6bdf2d35f24a1a6cb48c92b27`; `candidate.py` `b4a82fb0e84af75257f12364a9431e871110938574b5c77681bdea6bb56a53a9`; `audit.py` `acbcad524adf636a47695bb4cd13eb9db9df1ce805c47f5fefbd921b2043823a`; `test_recovery_rate.py` `c6be183c79f576fa51f68c4c1a87577bf8f1ccee3b69deb9f705c0bd44f68ad4`. The plan hash is intentionally omitted from its own embedded digest list.
