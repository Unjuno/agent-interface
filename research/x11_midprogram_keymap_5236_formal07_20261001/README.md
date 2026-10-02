# Issue #5236 Formal07 — fresh post-freeze successor

Formal06 is retained as `STOP_PROTOCOL_DEVIATION`: its raw output predates its issue freeze. Its auditor mismatch is diagnostic only. Formal07 is a distinct output allocation and must be frozen on Issue #5236 before its single Arch WSL2 invocation.

## H / T / D / C / U

- **H:** An XKB remap during a wait inside one preflighted X11 program can leave cached symbol mapping stale, causing later text to produce a wrong saved value.
- **T:** Exactly three fresh Arch Linux WSL2/private-Xvfb rows, in order: `control_us` (US, no actor), `jp_to_us` (JP→US), `us_to_jp` (US→JP). Each performs focus, move/click the fixture Entry at (50,55), type `a`, wait 1500ms while an actor sleeps 250ms then runs `setxkbmap`, type `_`, Ctrl-S, wait 250ms, and release. Output: `results/formal07-20261001-01`.
- **D:** Wrong completed remap saved bytes => `FAIL_STALE_MAP_EFFECT`; both remaps refuse at op 6 with verified empty release/no effect => `PASS_MIDPROGRAM_REMAP_FAIL_CLOSED`; both exact saved bytes => `NO_STALE_EFFECT_OBSERVED`; other/missing evidence => STOP. The control must save exact `{"saved": true, "text": "a_"}\n`.
- **C:** Each row uses a fresh private Xvfb, fixture, backend/session and output subdirectory. The program bytes and wait durations are fixed; only initial/target layout differs. Independent raw-only auditor plus six corruption controls.
- **U:** Synthetic Tk/Xvfb, two layouts, one keymap change during a fixed wait; no IME, groups/options, WSLg/Windows, or general GUI claim.

## Frozen runtime and execution boundary

Exact main base: `a7648fb47f16b15ac2fdb63075186aad1189859c`. Arch WSL2 runtime: CPython 3.14.5, Python-Xlib 0.33, Xvfb 21.1.24-1, setxkbmap 1.3.5-1, xkeyboard-config 2.48-1, Tk 8.6.16, libxss 1.2.5-1. Formal input is local Arch WSL2 only; Docker is used for CPU-only validation and never for formal rows.

`SOURCE_MANIFEST.json` pins the runner, audit, mutation controls, tests, backend, fixture, session, and `runtime/core_v1/contract.py`. The runner validates all blobs before creating its unique output directory. One invocation only, after the complete freeze comment is posted. On any STOP, retain evidence and do not retry or substitute a row.

## CPU-only validation

```sh
python -B -m unittest -v research.x11_midprogram_keymap_5236_formal07_20261001.test_formal
```

One-shot command, only after freeze:

```sh
python -B -m research.x11_midprogram_keymap_5236_formal07_20261001.runner --output research/x11_midprogram_keymap_5236_formal07_20261001/results/formal07-20261001-01
```

Audit raw and wrapper once only if runner returns 0; execute corruption controls once. Formal06 remains unchanged.
