# Issue #5236 — mid-program X11 keymap variant (Ubuntu WSL)

This is an additive, one-shot research harness for the hypothesis in GitHub Issue #5236. It does not modify runtime code. The authoritative issue requests Arch Linux / CPython 3.14.5; this host currently provides Ubuntu WSL / CPython 3.12.3, so any execution here is explicitly a separate environment variant and cannot be represented as the requested allocation. Docker commands are not used while the repository's active coordination hold is in force.

## H/T/D/C/U

- **H:** after whole-program preflight, a keymap changed externally during an in-program wait may leave python-xlib's cached map stale, so a suffix can be emitted with a wrong saved effect instead of failing closed.
- **T:** fresh private Xvfb/Tk fixture per row; one program types `http://`, waits 900 ms, types `a_b`, saves, and releases. Rows: unchanged US control, JP→US, and US→JP. A separate `setxkbmap` actor performs the remap during the wait. No patch or retry.
- **D:** derive only from raw per-case JSON, effect bytes, process receipts and wait/actor timestamps. Wrong completed effect → `FAIL_STALE_MAP_EFFECT`; both remaps safely refuse before suffix → `PASS_MIDPROGRAM_REMAP_FAIL_CLOSED`; exact completed effects → `NO_STALE_EFFECT_OBSERVED`; incomplete/provenance-invalid evidence → `STOP_PROVENANCE_OR_RUNNER`.
- **C:** same fixture application, runtime source, program, wait interval and save path across rows; unchanged-US control checks basic operation.
- **U:** one-shot deterministic transition probe only. No performance, general XKB, IME, or cross-distro claim. WSL/Python 3.12 result is not a substitute for the issue's Arch/Python 3.14.5 allocation.

## Frozen inputs and invocation

Base commit: `f65b39b6434714a08dfa743f8f16f5cae1667f6d`. Runtime source blobs are pinned in both scripts. The runner rejects different source blobs or a base not ancestral to HEAD. Intended command, to be recorded on Issue #5236 before the one-shot run:

```sh
python3 -B research/integration/x11_midprogram_keymap_5236_wsl_v1/runner.py --output research/integration/x11_midprogram_keymap_5236_wsl_v1/results/ISSUE5236-UBUNTU-WSL-20260928-01
```

Output path must not already exist. The auditor is a separate program and keeps its case constants locally rather than importing the runner. Run it once on frozen raw output; retain its output and SHA-256 manifest with the report. The result remains provisional until reviewed against Issue #5236's requested environment.

## Result

Not run yet. Construction, source/harness hashes, allocation record and one-shot result will be appended before reporting a conclusion.
