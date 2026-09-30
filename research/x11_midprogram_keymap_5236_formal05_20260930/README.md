# Issue #5236 formal successor 05

This additive allocation probes an XKB layout change during the wait between two keyboard operations in one admitted X11 program. It preserves allocation01 and formal02–04 STOP results and their evidence. Formal02 found the child import-path defect; formal03 found missing Tcl/Tk libraries; formal04's Docker diagnostic isolated a missing pointer click to focus the fixture Entry. The separate local Docker diagnostic found no saved effect without the click and `{"saved": true, "text": "a"}` with the click. This successor includes the Entry click and an auditor that validates the exact `-c`/runpy bootstrap and Tk preflight records.

## H / T / D / C / U

- **H:** a mid-program MappingNotify may leave the backend keymap stale after preflight, potentially producing a wrong saved value.
- **T:** three fresh rows (`control_us`, `jp_to_us`, `us_to_jp`) on Arch Linux WSL2, CPython 3.14.5, Python-Xlib 0.33, each with its own private Xvfb, fixture, backend and actor. Each program focuses the fixture, pointer-moves to Entry client coordinate `(50,55)`, left-clicks it, types `a`, waits 1500 ms while the actor changes JP↔US, types `_`, saves with Ctrl-S, then releases all inputs. The exact formal output allocation is `results/formal05-20260930-01`.
- **D:** wrong saved bytes in a completed remap row => `FAIL_STALE_MAP_EFFECT`; both remap rows refusing at post-remap operation index 6 (after Entry click, initial `a`, and wait) with verified empty release => `PASS_MIDPROGRAM_REMAP_FAIL_CLOSED`; exact saved bytes for both remaps => `NO_STALE_EFFECT_OBSERVED`; any missing or unplanned evidence => STOP. The control must also produce the exact saved bytes.
- **C:** fresh private X server/application per row; same program and wait; only target mapping changes. The independent auditor consumes raw records and wrapper records; five corruption controls must reject mutated evidence.
- **U:** does not cover IMEs, other XKB groups/options, changes during a single text op, WSLg/Windows desktops, or general GUI automation.

## Environment and boundaries

Formal execution is one-shot, local Arch Linux WSL2; Python 3.14.5, Python-Xlib 0.33, Tcl 8.6.16, Tk 8.6.16, and libxss 1.2.5. The runner checks that both `tkinter` and the fixture module import successfully before it creates the allocated result directory. No Docker, live WSLg display, network, GPU/model, or user data is used for formal rows. Docker is reserved for CPU-only tests of the harness, auditor and runtime unit tests. Never execute the formal rows in Docker because the target and namespace/socket checks are the Arch WSL2 host environment.

The runner refuses any output path other than the allocated unique path, verifies source blobs before creating output, and uses a private user+mount namespace with tmpfs at `/tmp/.X11-unix`. A single frozen invocation is permitted only after a matching freeze comment on Issue #5236. Any STOP is retained; no retry or row substitution.

## Local validation

CPU-only tests:

```sh
python -B -m unittest -v research.x11_midprogram_keymap_5236_formal05_20260930.test_formal
```

Frozen one-shot command (only after the GitHub freeze is posted):

```sh
python -B -m research.x11_midprogram_keymap_5236_formal05_20260930.runner \
  --output research/x11_midprogram_keymap_5236_formal05_20260930/results/formal05-20260930-01
```

Independent audit:

```sh
python -B -m research.x11_midprogram_keymap_5236_formal05_20260930.audit \
  research/x11_midprogram_keymap_5236_formal05_20260930/results/formal05-20260930-01/raw.json \
  research/x11_midprogram_keymap_5236_formal05_20260930/results/formal05-20260930-01/wrapper.json
```
