# Retained raw-JSON resume ingress boundary — Issue #4313

This is retrospective delivery of an already executed local pilot, not a new formal allocation or public preregistration. The original result is `PASS_LOCAL_INGRESS_BOUNDARY_CHARACTERIZATION`; it is **not a production safety PASS**. Correctly typed false-state receipts led to invalid continuation in every arm and remain explicit negative evidence.

## Read-only reproduction

From this directory, with CPython 3.13 and its standard library:

```sh
python -B verify_publication.py
```

This reconstructs all 558 original v3 files in a fresh temporary directory, verifies the original 557-entry manifest and 15-file local freeze, and runs only the retained raw-only audit and copied-evidence controls. The audit/control outputs must reproduce byte-for-byte. It never starts the GUI, policy worker or scientific runner.

For data-only restoration to a NEW trusted local destination:

```sh
python -B unpack.py /tmp/ingress4313-review
```

Do not rerun the consumed pilot runner. The unpacker rejects an existing destination, missing/changed/reordered parts, symlinks and inconsistent envelopes. It uses bounded expansion and writes regular relative files only. Its parent directory is trusted; it is not an adversarial filesystem sandbox.

## Contents and identities

`CAPSULE.json` describes 16 ordered Base64 text parts. They encode the complete 96,472-byte XZ archive with SHA-256 `2fd3a679908b7354252162a995e3606b2db85607db273f365c1d2bf96e345046`. The archive restores `research/integration/resume_json_ingress_c7e4_v3/`: 558 regular files, 2,191,841 member bytes, no sampled/truncated raw records. Original app/input/IPC/process records, local freeze, construction failures, rejected prefreeze, audits and historical publication limitation are unchanged.

`retained/` contains exact readable copies of selected original files. `REAUDIT_EXECUTION.json` and `REAUDIT.stdout` record this continuation's read-only verification. `PACKAGING_TESTS.json` records eight publication-helper rejection checks, not a new scientific experiment.

The original conversation ZIP is 1,441,495 bytes, SHA-256 `e13adb499573de545eb9ebb46e38917c343aed82fb8a045b5679445536d6dc7b`. Redundant outer patches and the embedded prior-v2 ZIP are not duplicated in this v3-only capsule. The preceding 264-file nested STOP and 65-file type-validation study belong to their separately owned publication lanes; this capsule does not claim their complete raw delivery.

See [REPORT.md](REPORT.md) for results, H/T/D/C/U, scope and integration decision. This directory is evidence-only and additive; no shared runtime, workflow, index or predecessor result changes.
