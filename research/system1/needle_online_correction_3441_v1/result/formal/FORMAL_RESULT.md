# Formal result — Issue #4824

## Disposition

**STOP_AUDIT — invalid formal allocation; no scientific PASS/FAIL/HOLD conclusion.**

The frozen trainer and independent auditor each ran once on the local machine.
The trainer exited 0 and emitted three seeds × nine checkpoints. The separate
auditor exited 1 with `STOP_AUDIT`. The allocation is consumed: no rerun, retry,
seed replacement, source correction, or audit relaxation is part of this result.

## Specific defect

The frozen specification defines held-out skill A as class 0 for every row.
In `runner.py`, `held_a_x, held_a_y = data(seed, 211, 256)` instead generated A
labels using the skill-B rule (class 1 iff feature 0 is 1). The independent
auditor regenerated the specified A labels and rejected each seed's held-out-A
identity and all nine A metric checkpoints: 30 audit errors total. It also
recomputed 13,824 predictions and rejected all 11/11 corruption controls.
These checks diagnose the invalid runner; they do not validate model behavior.

## Environment and execution

- Local Docker only; no external workflow, image pull, network, GPU, or package install.
- Image `needle-pilot05:local`, ID
  `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`
- `linux/amd64`, Python 3.12.14, PyTorch 2.5.1+cpu, CPU, one thread.
- Limits: one CPU, 2 GiB memory, 64 PIDs; read-only root/source.
- Seeds: 68117, 68229, 68341; fixed source and image as recorded in `FREEZE.json`.
- Formal trainer invocations: 1; independent audit invocations: 1.
- Construction check: 12 assertions passed, zero optimizer updates (not formal evidence).

## Evidence integrity

`raw.json` is the byte-for-byte trainer output; `audit.json` is the auditor output.
The raw file is stored as ordered binary chunks under `formal/raw_parts/` so the
original can be reconstructed by concatenating chunk files in ascending index
order. `formal/raw_parts/manifest.json` records total byte length, chunk lengths,
chunk SHA-256 values, and the whole-file SHA-256. No parsing/reserialization is
used for the archived raw bytes.

- Raw bytes: 1,177,496; SHA-256
  `6eac30fd8fbcb4d98ce93c44d8d71b0ae25d88d12a0f322a0b2db09f08a74d83`
- Audit JSON: 1,958 bytes; SHA-256
  `3ea6325e2f685fbd46d4967d28a4d9c0d4f9ccd2b8c38da5b0c486e1a8d94e34`
- Audit decision: `STOP_AUDIT`; 30 errors; 11/11 corruption controls rejected.

## Interpretation boundary

The observed `STOP_AUDIT` is an implementation/provenance defect, not evidence
for or against online correction, retention, or forgetting. Any corrected
experiment requires a separate successor issue, a new frozen source identity,
collision-checked seeds/path/branch, and a fresh one-shot allocation. The old
source and result must remain unchanged.

