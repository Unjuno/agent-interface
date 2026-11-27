# PR #8874 V4/V12 actual-Xvfb receipt composition A20

## Preregistered question

Does the V4/V12 owner path emit an owner-bound explicit-up verification receipt for a real XTEST `w` press/release on private Xvfb, and does that receipt stream satisfy the unchanged A18/PR #8857 retained-input analyzer without post-hoc enrichment?

## H/T/D/C/U

- **H:** V4/V12 will verify the key-up through exactly one identity-bound owner-thread `owner_explicit_keyup` record and the analyzer will accept the admission/release pair.
- **T:** One WSLc container, one isolated Xvfb display/window, one lowercase `w` down and up, independent Xlib KeyPress/KeyRelease observations and XQueryKeymap samples, V4/V12 records, analyzer over unmodified return objects. Save raw output and audit separately. Candidate invocation once; no retry.
- **D:** `PASS_METHOD_SCOPED` requires event pair, keymap down/up, verified V4 receipt, owner close/stopped/thread absent, Xvfb exit 0, analyzer ready with one hold, and integrity audit. If key-up is externally verified but analyzer rejects, `FAIL_ANALYZER_BRIDGE`. Setup/harness defects are `STOP`.
- **C:** Xvfb/XTEST proves only a virtual X11 server transition, not physical input or target application effects.
- **U:** No live desktop, Doom/MAP01, model call, threat exposure, recovery efficacy, or formal/live allocation. No changes to runtime sources.

## Frozen conditions

- PR #8874 source head `6d008b53e23fda4703c8f56c4ea1bd762e5d147b`; its exact V4/V12/V3/V10, executor and lease source snapshots are recorded in `SOURCE_MANIFEST.json`.
- Analyzer is copied byte-for-byte from the A18 frozen PR #8857 source snapshot at head `4536ebff7d71848dc86fbf1cdc4f54957eb9ce2d`.
- WSLc 3.0.1.0; immutable cached image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`; Python 3.14.8 linux/amd64.
- `--pull never --network none --cpus 1 --memory 512M --user 65534:65534`, read-only source mount, separate writable result mount, `--rm`. Host swap limits unsupported; no hard memory limit is claimed.
- The single candidate result is `results/a20-01/raw.json`; container `codex-wslc-pr8874-xvfb-a20-20261013`.

## Scope distinction

This is a fresh construction/integration test, not a rerun of A09. A09 tested owner close; A20 tests explicit up composed with the retained-input analyzer. A18 exercised a different V10 direct-wrapper path. No outcome here generalizes to untested backends or live game behavior.


A19 stopped before any input operation because the source volume lacked `lease.py`. A20 adds that exact dependency from the already-frozen A18 shared lease source; A19 records remain immutable.
