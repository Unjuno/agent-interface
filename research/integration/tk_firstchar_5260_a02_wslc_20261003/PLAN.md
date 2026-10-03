# WSLc first-character A02 implementation plan

> For agentic workers: use superpowers:executing-plans inline. The user's
> autonomous-work direction overrides repeated design/method approval gates.

**Goal:** execute one valid, bounded #5260 successor in WSLc and preserve
its first outcome for integration through PR/main.

**Architecture:** isolate all new sources/results under this package.
Use a local uniquely tagged X11/Tk image, once-only host receipts, a
candidate derived from A01, and a separate independently reconstructed audit.

**Tech stack:** Windows Python subprocess, WSLc, Debian Python/Tk, Xvfb,
Openbox, Python-Xlib, ImageMagick. Spec: `PREREG.md`.

## Global constraints

96 formal rows; 0/50/100 ms first-key delay; 20 ms gaps; payload hxy;
250 ms save gap; fresh app per row; no formal retries. Do not edit r0,
#5296 or A01. Keep remote publication batched except prospective freeze.

## Review focus

Output occupied -> refuse launch; executable missing -> retain failure;
false baseline hash -> reject; first-frame bytes differ -> reject;
coordinate methods coincide -> describe arithmetic, not API identity.

### Task 1: runtime construction

- [ ] Write `test_host_capture.py` for stdout/stderr/exit receipts,
  occupied-output refusal and launch failure; run RED.
- [ ] Implement `execute(argv: list[str], output: Path) -> dict`
  in `host_capture.py`; run GREEN.
- [ ] Build image from `image/Dockerfile` with receipts outside context.
  Inspect only the resulting image; record exact identity/versions.

Runtime observation: the selected system interpreter is Debian
Python 3.13.5/Tk 8.6, not the base image's separate /usr/local Python 3.12.
This new environment is part of A02's scope, not parity with A01.

### Task 2: candidate and independent audit

- [ ] Derive A01 source without changing originals.
- [ ] Write tests exposing baseline integrity omission and read-only input
  violation before correcting `audit.py`.
- [ ] Retain one uniquely allocated smoke's first outcome.
- [ ] Audit corruption copies; do not overwrite raw.

### Task 3: formal evidence and integration

- [ ] Freeze SHA-bound sources/image/argv/new outputs; prospective Issue
  allocation comment and source commit readback.
- [ ] Candidate once, auditor once; preserve all first outcomes, raw
  streams, receipts, warning and cleanup records.
- [ ] Add read-only packet verifier and retained-only CI; run package and
  repository checks. PR, verify expected head/CI and integrate.
- [ ] Verify main bytes/source ancestry; remove only owned remote branch
  after dependency checks; record results/resource release.
