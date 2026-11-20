# Formal allocation STOP audit: 2026-10-08

Status: `STOP_AFTER_FIRST_UNEXPECTED_CASE` at `C01`; eight scheduled cases were not started. No replacement or rerun is permitted under this allocation.

The exact source freeze was `d5732e6628a48481dd6cfc93297626811bdf528f` (freeze SHA-256 `48969b57f1be88ab8a9d8bcd039271978cd0488cc17384b724dce38b34406eb7`, source-manifest SHA-256 `d771a66b972953f59b4efb73db591f2b517123997f885c705d6cca31f7b8056a`). The network-isolated preflight passed with Xvfb `:99`, XTEST present, two exact pinned warning blocks, and clean socket/lock removal. `C01` used a fresh Xvfb `:99`; Xvfb and probe both exited 0, probe stderr was empty, all processes cleaned up, and the independent before/after snapshots showed LockMask 0 and a neutral 32-byte keymap.

The raw record SHA-256 is `899f1fa5883c0563f458aae42da7f56ab3157c4c5699d71c9ea06c91a84289e3`; supervisor SHA-256 is `d552e169e3266bce34f1b208fae9fa617a824b8547c28a9d78e082bf43a0309f`. The public program completed operations `[0, 1, 2]`, returned status `completed`, and reported a verified neutral release receipt. The Tk Entry ended at `aB2`.

STOP came from an auditor predicate defect, not from a contradictory observed value: `audit_record()` compared every `KeyPress.char` to `list("aB2")`. The valid `Shift_L` modifier press is journaled as a `KeyPress` with `char: ""`, so the observed list is `['a', '', 'B', '2']`; it also incorrectly counts four KeyPress events against three character releases. The raw journal has three character-producing presses (`a`, `B`, `2`) and releases each of those plus Shift. This explains the two STOP errors in `RAW_INDEX.json` and is not a scientific FAIL or PASS.

The allocation stopped immediately as preregistered. Do not infer anything about the two guard arms from this run. A future allocation requires a separately reviewed protocol revision with auditor fixtures that include modifier events, a new immutable freeze, and a new allocation; this run must remain unchanged.

## Raw artifacts

`RAW_INDEX.json`, `PREFLIGHT.json`, `preflight-xvfb/`, and `C01/` are the exact recovered VM outputs. Their hashes are recorded in `RAW_SHA256SUMS.txt`.
