# Effect receipt handoff — current-main recheck (2026-11-23)

## Scope and source

- Current fetched main: `1109a62ffd51ddf6888cc72be43a343f3ce0b550`.
- Reused implementation/evidence: `effect_receipt_handoff_v1.py`,
  `test_effect_receipt_handoff_v1.py`, and
  `effect_receipt_handoff_20261121/`.
- Source Git blob hashes are recorded in the retained packet's
  `source-sha256.txt`; evidence bytes and saved source hashes were rechecked
  against `SHA256SUMS.txt` / current main.
- Python: Windows CPython 3.11.9.

## Re-execution

The exact 42-test command set from the retained conditions was rerun against
the existing handoff worktree with its required module search path set to the
ledger directory. Normal mode passed 42/42 (`exit=0`, 30.145 s); optimized
mode passed 42/42 (`exit=0`, 32.381 s). It covers the receipt adapter,
recorded-comparison adapter, and comparison-measurement validator.

An initial invocation omitted that `PYTHONPATH` and failed before test
execution with three `ModuleNotFoundError` import errors. This was a harness
invocation error; the corrected invocation above passed. No code or pass
criterion was changed.

## Result and boundary

The synthetic contract remains reproducible: a retained independent score and
capture interval can be joined to the same public action, native release, and
neutral-horizon identity; post-horizon factual success remains ineligible;
unknown/ambiguous timing and stale identity fail closed; the result composes
with the matched-block validator. This is offline evidence only.

It does not prove a live provider request/usage, live GUI effect, recovered
task success, MAP01 completion, repeated reliability, matched integrated
efficiency, distributable runtime acceptance, or Research Preview graduation.
The caller-lifecycle follow-up test commit
`ae10f768a8ed2dfe4d8a626ead25039842e88f87` is not an ancestor of current main;
its additional history must be reconciled against merged PRs before any new
implementation. GitHub search showed PR #10437 and #10444–#10446 merged for
adjacent handoff stages; no duplicate implementation was started.

## Related isolated UI observation

Windows Chrome was launched by WSL into a dedicated temporary user-data
directory with `about:blank`. The app inventory contained exactly one Chrome
window (`about:blank - Google Chrome`) and separately identified a
Lightbrowse window (`Example Domains — Lightbrowse`) that visually overlapped
the screenshot. No tab, input, network navigation, or personal browser state
was used. This confirms WSL-to-Windows process/window visibility for this
isolated Chrome instance only. It is not a computer-control runtime task,
target-specific capture, input/release test, or latency comparison.

The setup wrapper was first invoked with incorrect path interpolation and
failed before launching Chrome; no trial was performed by that failed
invocation. The corrected headless `about:blank` command exited 0 (41-byte
DOM, empty stderr), then the headed isolated Chrome window was observed. These
outcomes remain separate.

## Follow-up

1. Reconcile the unmerged caller-lifecycle commit and all related PR heads with
   current main; avoid duplicate implementation.
2. If it adds a genuinely missing contract case, port only that case onto a
   fresh clean current-main worktree and preserve normal/-O raw output.
3. Keep #57 open until a fresh authorized live standard-caller experiment
   supplies identity-bound effect, release/horizon, all-attempt provider
   usage, latency, and correctness evidence with repetition.


## Post-merge exact-main recheck (2026-11-23)

After PR #10490 merged, the handoff source/test paths were confirmed unchanged from the test base through main `7e9caab2acf8428beeb48682edd5e7a0bace4967`. A clean detached worktree at that exact main SHA reran the three relevant modules with `PYTHONPATH` set to the ledger directory. Windows CPython 3.11.9 passed **60/60 normally** and **60/60 under `-O`**. Full stdout logs are retained in `raw/handoff-current-main-normal.txt` and `raw/handoff-current-main-optimized.txt`.

This strengthens reproducibility on merged main but remains synthetic adapter/comparison evidence. It does not establish live provider accounting, task effect, repeated recovery reliability, or the integrated all-attempt efficiency result required by #57.
