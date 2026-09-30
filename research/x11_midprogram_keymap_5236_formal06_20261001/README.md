# Issue #5236 formal successor 06

This additive allocation probes an XKB layout change during the wait between two keyboard operations in one admitted X11 program. It preserves allocation01 and formal02–04 STOP results and their evidence. Formal02 found the child import-path defect; formal03 found missing Tcl/Tk libraries; formal04's Docker diagnostic isolated a missing pointer click to focus the fixture Entry. The separate local Docker diagnostic found no saved effect without the click and `{"saved": true, "text": "a"}` with the click. This successor includes the Entry click and an auditor that validates the exact `-c`/runpy bootstrap and Tk preflight records.

## H / T / D / C / U

- **H:** a mid-program MappingNotify may leave the backend keymap stale after preflight, potentially producing a wrong saved value.
- **T:** three fresh rows (`control_us`, `jp_to_us`, `us_to_jp`) on Arch Linux WSL2, CPython 3.14.5, Python-Xlib 0.33, each with its own private Xvfb, fixture, backend and actor. Each program focuses the fixture, pointer-moves to Entry client coordinate `(50,55)`, left-clicks it, types `a`, waits 1500 ms while the actor changes JP↔US, types `_`, sends Ctrl-S, then explicitly waits 250 ms before release/teardown. Exact output allocation: `results/formal06-20261001-01`.
- **D:** wrong saved bytes in a completed remap row => `FAIL_STALE_MAP_EFFECT`; both remap rows refusing at post-remap text operation index 6 with verified empty release => `PASS_MIDPROGRAM_REMAP_FAIL_CLOSED`; exact saved bytes for both remaps => `NO_STALE_EFFECT_OBSERVED`; any missing or unplanned evidence => STOP. The control must also produce the exact saved bytes. A completed row must retain both wait receipts, including the post-save 250 ms wait.
- **C:** fresh private X server/application per row; same program and wait; only target mapping changes. The independent auditor consumes raw records and wrapper records; six corruption controls reject omitted row, swapped direction, wrong expected bytes, absent actor receipt, missing post-save wait, and changed raw output.
- **U:** does not cover IMEs, other XKB groups/options, changes during a single text op, WSLg/Windows desktops, or general GUI automation.

## Environment and boundaries

Formal execution is one-shot, local Arch Linux WSL2; Python 3.14.5, Python-Xlib 0.33, Xvfb 21.1.24-1, setxkbmap 1.3.5-1, xkeyboard-config 2.48-1, Tcl/Tk 8.6.16, and libxss 1.2.5. The runner checks fixture imports before creating the allocated result directory. No Docker, live WSLg display, network, GPU/model, or user data is used for formal rows. Docker is reserved for CPU-only tests. Never execute formal rows in Docker.

The runner refuses any output path other than the allocated unique path, verifies source blobs before creating output, and uses a private user+mount namespace with tmpfs at `/tmp/.X11-unix`. A single frozen invocation is permitted only after a matching freeze comment on Issue #5236. Any STOP is retained; no retry or row substitution.

## Local validation

CPU-only tests:

```sh
python -B -m unittest -v research.x11_midprogram_keymap_5236_formal06_20261001.test_formal
```

The same host-only suite is also exercised in the local Docker image during construction; Docker is not used for formal rows.

Frozen one-shot command (only after the GitHub freeze is posted):

```sh
python -B -m research.x11_midprogram_keymap_5236_formal06_20261001.runner \
  --output research/x11_midprogram_keymap_5236_formal06_20261001/results/formal06-20261001-01
```

Independent audit:

```sh
python -B -m research.x11_midprogram_keymap_5236_formal06_20261001.audit \
  research/x11_midprogram_keymap_5236_formal06_20261001/results/formal06-20261001-01/raw.json \
  research/x11_midprogram_keymap_5236_formal06_20261001/results/formal06-20261001-01/wrapper.json
```

