# Issue #4563 controlled-boundary raw audit addendum — 2026-09-28

## Disposition

`PASS_RAW_AUDIT` for the three retained controlled timestamp-injection rows; this does not upgrade the original scoped boundary result or diagnose the natural #4544 inversion. Separately, current-main construction reproduction is `STOP_DEPENDENCY_PATH_INCOMPLETE`; the two affected construction tests do not run to their assertions in the checked-out main tree or in the pinned container.

## H / T / D / C / U

- **H:** The retained −1/0/+1 ns JSONL rows and summary agree with each other and with the corresponding typed observation source events; the audit can establish exact boundary arithmetic and retained owner-release evidence without importing the candidate monitor or replay gate.
- **T:** A new standard-library-only raw auditor reads the existing immutable `-02` summary/rows, seed-990643 preflight event/release evidence and pinned hashes. It independently reconstructs each case and requires exact outcome, guard receipt, source event sequence/timestamps, and null calibration fields for this injected-clock replay. Twelve effective field-mutation controls challenge the auditor.
- **D:** OrbStack `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`, linux/arm64, no network, read-only root/source, 0.25 CPU, 256 MiB, 32 PIDs. Auditor decision `PASS_RAW_AUDIT`, errors `[]`; the independent mutation suite passes 2 tests and rejects 12/12 field mutations. Host repeat agrees. Existing hashes match the recorded values for summary, three raw rows, source event stream, owner-release list and environment manifest.
- **C:** Same retained observation and output bytes; no candidate code is imported by the auditor. Delta is recomputed from integer timestamps; source sequence/capture/typed-ready/emit values are read from the preflight event stream. All three releases are verified with empty key/button sets. The controlled replay asserts a logical `INPUT_ACTIVE` receipt; it is not evidence of physical input or release in those replay cases.
- **U:** The typed observation came from a real zero-model Docker MAP01 session, but the −1/0/+1 decision timestamps were injected. Calibration fields are null in the replay. No natural clock inversion, model call, physical input, task progress, held-input occupancy, useful feedback or recovery policy was tested.

## Current-main construction STOP

The focused suite command is:

```sh
python3 -B -m unittest research.doom.map01_policy_invalidation_clock_4559_v1.test_diagnostic_capture -v
```

On host Python 3.14.5 and again in the pinned Linux/arm64 image, 3/5 tests pass and 2/5 fail before their assertions. The host failure is `ModuleNotFoundError: PIL`; the pinned-container failure is `ModuleNotFoundError: action_validity_admission_v1` while `adapter_v13.py --prepare-only` walks the retained v12/v10/v3 dependency chain. No package installation, source rewrite, formal seed, model request, or GUI action was attempted. This does not negate the historical construction and controlled replay evidence already recorded in `EXPERIMENT_20260927.md` / `REVALIDATION_20260927.md`; it records that the current checkout's focused reproduction is not self-contained.

## Validation and hashes

- `test_audit_controlled_boundary_v13.py`: 2/2 pass; the negative-control test rejects 12/12 mutated fields.
- The auditor ran separately in OrbStack and on the host: `PASS_RAW_AUDIT`, errors `[]`.
- `git diff --check`: pass.
- Auditor SHA-256: `0d85dbb33cdc443ff820c8537df8b8f589aa2dd7273b7fa6d99a177c6c62f57d`.
- Auditor test SHA-256: `821d539e1d2b3ef66757a13e377d324731f09804ea5bd308b6af3182c1d39334`.
- Existing output SHA-256 values are recorded in `REVALIDATION_20260927.md`; this addendum does not modify those outputs.

This addendum is an audit and reproducibility qualification only. It does not close #4563 or satisfy the current #59 held-input/useful-feedback/recovery objective.
