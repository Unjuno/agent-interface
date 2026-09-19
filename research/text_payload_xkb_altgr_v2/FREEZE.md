# Source-first formal freeze

Task: `XKB-ALTGR-DIRECT-PREFLIGHT-20260916-002`, Issue #360.
Publication BASE: `ddc07847f163d0b57fe409f5bc89ca083da1b670`.
No scored/formal XTEST input has run under this task at this freeze.

## Why this is task 002

Issue #355 / task 001 was stopped before formal execution because its post-issue development construction exceeded that issue's stated construction allowance. The extra construction observations remain excluded design knowledge; they are not pooled into this formal block. Task 002 explicitly preregisters them and allows no additional development input before this source freeze.

Excluded known construction from #355: `@` and `A@[]\\{}|~Z` delivered exactly on a private four-level/Mode_switch fixture; `^`, backtick and `A^Z` refused with zero emissions. No threshold was selected from those observations.

## Frozen mechanism

Only one capability is added relative to the retained #328 direct-key idea: Group1 levels 2/3 can be selected using one dedicated `Mode_switch` keycode placed in Mod5. Printable ASCII still requires a direct keysym. Dead keysyms, Compose, IME, Unicode outside printable ASCII and extra groups are not lowered.

The candidate binds both the complete keyboard mapping and modifier mapping before input. Whole-payload `prepare()` completes before any XTEST emission. Rejection therefore must have zero emissions and empty receiver text. Accepted strokes must independently correspond to the retained core-map keycode/level and end with an empty physical state.

## Frozen environment/source identity

Installed German XKB resolved during excluded construction has SHA-256 `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`. Every formal fresh Xvfb must resolve to this exact byte hash or the block is `SETUP_DRIFT`; do not substitute another layout/source.

Formal schedule SHA-256 is `dd0ac2b4cac1dc22642ef876d2a01bdb5ad456a8b31a59fe31b58af67caa63b8`. Source SHA-256 identities are frozen inside `prereg.json` for `candidate.py`, `projection.py`, `receiver.py`, `run_arm.py`, `run_block.py`, `audit.py`, and `test_audit.py`.

## Formal allocation

Exactly three fresh `xvfb-run` servers. Exactly sixteen frozen payloads per server in the three fixed orders in `schedule.json`: 48 trials total. Controls: `a`, `A`, `?`; historical two-level rejects `@ [ ] \\ { } | ~ ^ backtick`; one all-direct mixed payload; two direct dead-key controls plus two mixed payloads containing those dead-key controls.

Historical #328 two-level reject set must be reproduced from the resolved XKB itself. Candidate recovery set is frozen as `@ [ ] \\ { } | ~`; `^` and backtick must remain non-direct and fail before input.

No retries, case replacement, schedule extension, source repair, payload changes, layout changes or threshold tuning after the first formal server starts. The independent auditor does not import candidate/projection code. Offline corruption tests may consume retained formal bytes only; they may not launch another measured block.
