# Current-head V15 per-key owner identity recheck

This follow-up reruns the previously reported V15 per-key owner-selection probe against PR #8065's latest head, `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`, based on current main `11445a7ca200404ddc80bf7ebb1dbef86eb059de`.

The bundled Python run reproduced the mismatch: V12-perkey selected the archived A01 owner; default V15 selected the current V4 transition owner; V15-perkey selected current raw `research/live_control/input_owner_v12.py`, while the source manifest recorded the archived A01 owner hash. The startup selection boundary completed in all three routes, but no session or owner was instantiated. The probe's Xlib, VizDoom, process, and thread constructors were replaced with fail-fast stubs.

The first attempt with system Python stopped before the boundary because Pillow was unavailable. That STOP is retained. The same frozen probe and source closure then ran successfully with the desktop-bundled Python 3.12.14 / Pillow 12.3.0. No dependency was installed.

This is source-selection evidence only. It establishes no KeyRelease, server keymap state, physical release, application consumption, live game/input, threat reaction, task effect, recovery, or MAP01 outcome. The source-derived missing-UP concern in PR #8079 remains distinct from the executed startup selection result.

See `PLAN.md`, `FREEZE.json`, `source-manifest.json`, `source-snapshots/`, `results/`, and `audit.py`. The candidate was reconstructed exactly from the frozen PR head and independently audited without importing the probe.

## Reproduction

The auditor compares retained bytes with the pinned PR #8065 commit using `git show`. In a clean clone that commit may not be present yet. Fetch and verify the frozen PR head before running the auditor:

```sh
git fetch origin refs/pull/8065/head
test "$(git rev-parse FETCH_HEAD)" = "4158d9b063e7cbf56828f1b0667ec2714af0ff2b"
python3 -B audit.py
python3 -B replay_startup.py /tmp/v39-owner-recheck-new-output
```

Use CPython 3.12 with Pillow available. The retained run used the Codex desktop bundled Python 3.12.14 / Pillow 12.3.0 recorded in `RUN.json`.

The replay refuses an existing output directory. It materializes the 56 retained exact snapshots, launches three fresh processes, and stops before owner/session construction. Two snapshots are base64-encoded solely to preserve exact source bytes while keeping `git diff --check` clean; the replay decodes and verifies each frozen SHA-256 before use.

## Current-main relevance check

Main advanced to `22e25aa74cac30f629209555ba93ba3cd2a279f3` after the tested PR head was frozen. `CURRENT_MAIN_RECHECK.json` records a byte comparison of the source closure against candidate base `11445a7ca200404ddc80bf7ebb1dbef86eb059de`: all 55 shared source paths are unchanged; the only path absent from both base and current main is the candidate's new selection helper. The independent auditor checks this comparison. The original failed v0 comparison and audit are retained as previews; v1 classifies the helper as candidate-only and passes 22/22 checks.

## Current-main refresh (2026-10-05)

After the original closure check at `22e25aa74cac30f629209555ba93ba3cd2a279f3`, main advanced to `1fa854d537bfd711b5dfd99f8c04ab6c35bad286`. The same 56-path frozen source closure was compared byte-for-byte against its candidate base `11445a7ca200404ddc80bf7ebb1dbef86eb059de`: all 55 shared paths remain identical; the one helper path remains candidate-only; no path is missing or changed. `CURRENT_MAIN_RECHECK.json` records this refresh. The original 22e25 audit output is preserved as `results/AUDIT.at-main-22e25.json`; the current audit is regenerated without rerunning the probe. The candidate startup results, source freeze and failed system-Python STOP remain unchanged.

This refresh supports relevance of the frozen candidate-source finding to the latest main closure only. It does not mean the defective candidate was merged, does not establish execution on current main, and does not add any live-control or game-effect result.


## Latest-main refresh (2026-10-05)

Main advanced from `1fa854d537bfd711b5dfd99f8c04ab6c35bad286` to `f1d7dd1da44cad3e5fd22a65d7bec21d40289d1d`. The frozen 56-path candidate closure was byte-compared again against the candidate base `11445a7ca200404ddc80bf7ebb1dbef86eb059de`: all 55 shared files remain unchanged, the candidate-only selection helper remains absent from both base and main, and no path changed or went missing. `CURRENT_MAIN_RECHECK.json` records the latest comparison. The prior current-main audit is retained as `results/AUDIT.at-main-1fa.json`; the updated audit checks the same retained raw and snapshots. The startup probe was not rerun.

Main also retains separate A03 fake-X evidence for a dropped explicit KeyRelease in the batch path, while its A04 production per-program cleanup attempt stopped before the cases. That work does not alter this result: this package tests owner selection on the unmerged #8065 candidate; it does not test key-release execution or current-main gameplay.

## Latest-main refresh (2026-10-05, `19a6b723e58ccfd2b8265e88659589ef9223fcc9`)

The latest-main static comparison is in `CURRENT_MAIN_RECHECK_LATEST.json`, independently regenerated by `audit_latest_main.py` and summarized in `results/AUDIT_LATEST_MAIN.json` (7/7). Of the 55 paths shared with candidate base `11445a7ca200404ddc80bf7ebb1dbef86eb059de`, 54 remain byte-identical; `research/live_control/input_owner_v12.py` changed. `session_map01_v15.py` is unchanged. The current owner SHA-256 is `f4c7f00817343c675f889a6f974ff5e2177a9e7ffbe47c0576b5f0174c2da3bc`, still distinct from the archived A01 identity `b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508`. The candidate-only selection helper remains absent from main.

The frozen candidate audit remains 22/22 in `results/AUDIT.json`. Neither the candidate probe nor a current-main runtime was rerun. These records support the source-selection construction result against the frozen candidate and a latest-main static identity comparison; they do not establish that the helper executes on main or prove a gameplay/input effect, release, recovery, or MAP01 outcome.
