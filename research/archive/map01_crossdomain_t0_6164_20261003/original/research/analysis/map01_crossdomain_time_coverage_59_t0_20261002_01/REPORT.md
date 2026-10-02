# r133 cross-domain time-coverage identifiability T0-01

## Disposition

**Candidate: `HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED`. Independent audit: `FAIL_AUDIT`.** The candidate withheld a cross-domain time-coverage value, as required. The audit failure is a frozen expected-count defect, and the candidate output also contains an OpenTTD record-count inconsistency. Preserve this allocation as failed audit evidence; do not repair or rerun it in place.

## H / T / D / C / U

- **H:** A common time-weighted useful-control-coverage measure transfers from DOOM to OpenTTD only if every counted actuation has identity-bound physical down/up observations on one clock, an independently scored useful-effect observation joined to that actuation/clock, and a compatible denominator.
- **T:** Read-only replay of six SHA-256-frozen DOOM v38/v39 and OpenTTD event, observer, analysis, and audit inputs. Candidate once, then a separately authored raw-only auditor once. Eight construction tests ran before the allocation. No model, GUI, game, OS input, container, WSL, or GPU use.
- **D:** The candidate returned `HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED`, exit 0. The independent auditor returned `FAIL_AUDIT`, exit 1, because its expected v38 `post_control_score` count is 0 while the immutable trace has 1. It correctly reconstructed the remaining DOOM/OpenTTD counts, transition index, and source hashes.
- **C:** Frozen current-main observation: `a39606e9ea31d9eb56aa1a4591f7577a4e195656`; historical input commit `279ee4aee96c5646360239409931821726566aa2`. All six input Git blob IDs at the historical commit were re-read through GitHub MCP and matched current main; local SHA-256 values match `FREEZE.json`.
- **U:** Candidate OpenTTD output says `observer_records=1` and `observer_record_count=263`; only the latter matches the raw observer stream. The audit does not catch this inconsistency. No common time denominator is identified. This does not measure physical held duration, useful-feedback latency, matched recovery efficacy, human tempo, safety, task completion, or MAP01 exit.

## Retained measurements

- DOOM v38: 11 input admissions and 11 held-key records, no per-press up record; 27.489 s model wait, 11.418 s motor-capable program envelope, 16.022 s coast envelope, 0.049 s uncovered tail; 2/6 completed answers, 1/6 plan admissions, no MAP01 exit.
- DOOM v39: 39 input admissions and 28 held-key records, one program release but no per-press up record; 43.318 s model wait, 21.821 s motor-capable envelope, 21.484 s coast envelope, 0.013 s uncovered tail; 5/6 completed answers, 3/6 plan admissions, no MAP01 exit.
- OpenTTD: 2 keyboard admissions plus 7 pointer button-down admissions; 0 button-up admissions; 7 same-program verified-neutral terminal joins; 263 observer records, 2 unique states, one A-to-B transition at index 91. The observer has no shared host-clock or action-identity field.

The program-envelope values are not physical occupancy. A neutral terminal receipt is not a per-actuation release timestamp. The OpenTTD state transition is independently observed but cannot be joined to actuation time. These quantities are therefore not collapsed into a common percentage or duration.

## Immutable execution record

Allocation `R133-CROSSDOMAIN-TIME-COVERAGE-59-T0-20261002-01`; candidate=1, auditor=1, retries=0. `FREEZE.json`, `candidate_result.json`, and `audit_result.json` are preserved. Candidate exit 0; auditor exit 1. The failure is an auditor expectation defect, not a refutation of the scientific hypothesis. A corrected attempt requires a distinct additive successor that also checks candidate fields against independently reconstructed source counts.

## Reproduction

In a repository checkout, run `python3 download_inputs.py`, then `python3 -m unittest -v test_candidate test_independent_audit`. Only after checking `FREEZE.json` and input hashes, run `python3 run_candidate.py` once and `python3 independent_audit.py` once. The historical inputs are fetched from their immutable source commit; no live runtime is invoked.
