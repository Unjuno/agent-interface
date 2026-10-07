# A05 corrected X11 routing control

This package follows A04's retained `FAIL_AUDIT` without modifying or rerunning it. The new frozen candidate reads Python-Xlib 0.33 `event.window` and compares a direct XTEST control with the pinned InputOwner v10 on a focused Xlib client in an isolated OrbStack guest.

The pre-candidate protocol and gate are in [PLAN.md](PLAN.md) and [FREEZE.json](FREEZE.json). Exact guest/package facts and the no-input setup check are in [ENVIRONMENT.json](ENVIRONMENT.json), [SETUP.json](SETUP.json), and `results/A05/setup.stdout.txt`. The one candidate's raw record, command receipt, and scoped auditor result are in `results/A05/`; the brief disposition and limitations are in [RUN_RESULT.md](RUN_RESULT.md). `EVIDENCE_MANIFEST.json` binds the retained package files.

The successful result establishes virtual event routing and a minimal client's counter increment. It does not establish a Freedoom action, useful feedback, host-model behavior, live recovery, or the full #59 gate.

## Reproduction boundaries

The candidate ran once in OrbStack machine `v39-x11-routing-a05-20261004` (machine ID `01M42N2F303RHWR42A763DRBNJ`), Ubuntu 24.04 arm64, Python 3.12.3, Python-Xlib 0.33-2, Xvfb 21.1.12-1ubuntu1.8. The host package cache was not used; the installed package versions are captured in the environment record. The candidate made no network calls; Xvfb TCP listening was disabled. No effective CPU or memory cap was verified.

The frozen guest command was `python3 -B candidate.py --out results/A05/raw`. The host copy of the resulting raw file matches the guest SHA-256 recorded in `results/A05/RUN.json`. After candidate exit 0, the raw-only auditor ran once as `python3 -B audit.py --raw results/A05/raw.json --out results/A05/AUDIT.json`. The distinct `RAW_REVIEW.json` is a read-only `jq` projection and check of that retained raw. Candidate and auditor retries are prohibited.
