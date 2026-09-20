# Issue #3575 — XRes incarnation guard, provenance-complete successor

**Formal allocation 04: `PASS_PROVENANCE_COMPLETE_XRES_GUARD_REPRODUCTION`**, independently reconstructed in one pinned linux/arm64 OrbStack container allocation. This is one private-Xvfb fixture result only; it is not a production/default-runtime, general X11, or remote-X11 security claim. Issue #3555 v1 and every failed/held successor allocation remain unchanged.

## H/T/D/C/U

- **H** — A stale visual alias bound to p1's XRes `LocalClientPID` plus `/proc` start ticks is refused before native input after p2 reuses the same XID, geometry and exact pixels.
- **T** — Observe/mint p1; capture p1 XRes identity and exact window bytes while it is alive; stop p1; create p2; prove same XID/geometry/pixels but different PID/start ticks; make one stale-alias decision; only after safe refusal run one fresh p2 control.
- **D** — Per-allocation freeze/source manifest, immutable raw JSON, source and image hashes, fixture and runner, independent raw-only auditor with mutation controls, supplementary image/release/cleanup audit, and allocation stop/hold records.
- **C** — Private Xvfb over one fixed image; XRes PID is corroborative and start ticks are mandatory. No remote transport, production runtime, broad GUI reliability, or product-security inference. No retries within any allocation; each attempt has a distinct retained allocation ID.
- **U** — Reproducibility across independent allocations/hosts, TOCTOU races at the actual X11/native-input boundary, remote X11, and production integration remain open.

## Formal allocation 04

- Main source SHA: `c3abca57cb9d0e5cfea49794e35b33a84337959f`
- Container: `sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`, linux/arm64, `--network none`, read-only source, private Xvfb `:89`.
- Freeze SHA-256: `f3b4055f11795e962eb1bf59cf83de7c9cd3b5daa0206b6814ad560e4090b440`
- Source manifest SHA-256: `09344719083872cbad3ea063ecd6258308ba2f831c4b18df7c716985bf0ad410`
- Raw SHA-256: `cc6b54ed81c7893052f49a3b428fe3ba61e9c915bc0fe86beaca69372f168b34`
- Independent raw-audit SHA-256: `2577b2b72d6bb5971a973ad5b898281e99678049fa1c596140f31319f5a0bc7b`
- Supplemental raw/artifact audit SHA-256: `51a602c669e19192f299d9c4453508fb2db3d83777d55e8ce55ba3238f2b4f58`

Main subsequently advanced to `befe9212` while this record was being prepared. The seven-commit comparison changes X11 text symbol mapping for `=`/`*` but not the pointer-click path exercised here; integration is based on that current main and retains the exact `c3abca57` experiment freeze.

The measured p1 bytes were captured before p1 exit (capture monotonic ns `3687198035010`; p1 exit observed `3687201633457`; p2 start observed `3687206790148`). p1 and p2 both used XID `2097152`, geometry `[80,80,240,160]`, and 153600 bytes with SHA-256 `3b80132900d7ab9ce6a54b7f01b7fa0d345dd50aafb69135b740ae655c3aba0c`. XRes/process identities were p1 PID/start ticks `22/368714` and p2 `25/368720`.

The stale p1 alias was refused as `PROCESS_INCARNATION_MISMATCH`; `bridge.click` was not entered, backend emissions stayed at zero, and p2 effect stayed `[0,0,0]`. Only after refusal, the fresh p2 alias control completed with effect `[1,212,118]`, three backend emissions, and verified empty key/button release. Both fixture processes exited with code 0 and the bridge closed. The independent raw-only audit passed all 10 mutation controls; the separate supplemental audit verified the timing relation, release/cleanup, and all six PNG hashes.

## Predecessor allocation outcomes

- **01 — STOP_BEFORE_INPUT:** runner import failed (`ModuleNotFoundError: runtime`) before fixture start. No input; no retry.
- **02 — STOP_BEFORE_INPUT:** p1 fixture started, then bridge construction stopped on an omitted main-source dependency (`runtime.backends.x11_v1.capture_artifacts`). No stale-alias decision or input; raw/stderr retained; no retry.
- **03 — HOLD_AUDIT:** candidate gate and audits labeled PASS, but both purported p1 and p2 pixel reads happened after p2 reused the same XID. The p1 pixel precondition was therefore not established. Raw and original audits are retained unchanged; the post-run reassessment records the limitation.

See [REPORT.md](REPORT.md), [formal-04 raw evidence](formal-04/raw.json), and the [independent audits](independent-audit/formal-04/).

## Independent allocation 05 — Issue #3662

A separate OrbStack/private-Xvfb allocation and its frozen raw/audit are retained at [formal-05-independent-issue3662](formal-05-independent-issue3662/). Its freeze, source, allocation ID, raw, and audit hashes differ from formal-04; see its `REPORT.md` for the bounded result and the initial auditor-CLI usage failure. The historical `artifacts/formal_01/` output path is occupied by immutable evidence, so do not rerun this package in place. The archived freeze/reproduction instructions are historical; any new run requires a successor allocation, a new output path, and a new freeze. This evidence does not widen the one-fixture scope or promote the guard to runtime policy.
