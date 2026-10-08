# Current-main refresh and preservation audit — 2026-10-07

## Scope and source identity

- Current `main`: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`.
- Evidence-rescue branch refreshed by merge commit `dbfa95ff3`; the README
  conflict was resolved by retaining both the rescue entry and the newer main
  index rows. No retained experiment result or frozen source was rewritten.
- The original implementation PR #7440 still does not compose cleanly with
  current main. `git merge-tree origin/main refs/remotes/pr/7440` reports
  add/add conflicts in `research/doom/session_map01_v14.py`,
  `research/doom/session_map01_v15.py`,
  `research/live_control/input_owner_v12.py`, and
  `research/live_control/input_transition_owner_v4.py`. The rescue remains
  evidence-only; none of that implementation is promoted.

## Local checks

- `python3 -B research/check_workspace_index.py --git-tree` — PASS; 160
  top-level directories reachable.
- `git diff --cached --check` is clean for all non-archival changes. The full
  check reports exactly two pre-existing blank-at-EOF lines in the archived
  `freeze_hold_bound.py` and `run_hold_bound_30.py` source copies; both files
  were moved byte-for-byte and their frozen SHA-256 identities verify. Those
  historical bytes were not whitespace-normalized.
- `verify_preserved_hold_bound_30.py` — PASS 46/46, read-only. It validates
  the original package checksum list by resolving the moved historical
  writers/README to byte-identical archive copies, verifies the freeze-source
  hashes, and cross-checks the retained raw/audit/run receipt hashes.
- `python3 -B -m unittest -v test_preserved_evidence_safety.py` — PASS 2/2.
  Historical writer entry points and the safe-run guard refuse execution, and
  frozen output hashes are unchanged before/after.
- `check_current_main_sources.py` — read-only: 8/11 frozen
  `research/live_control/` sources match current main; `executor_v12.py`,
  `input_owner_v12.py`, and `input_transition_owner_v4.py` have drifted. The
  exact historical files remain preserved; no current-main behavior is
  inferred from their older run.
- The #7468 original self-referential manifest was not edited. Its direct
  verification still has the expected single self-entry mismatch; the
  separate `SHA256SUMS.RESCUE` verifies all eight non-manifest artifacts.
- Historical #7468 outcomes (18/20 parent-only and 20/20 with the publication
  barrier) and the earlier current-main spot checks at `69dd261` were not
  rerun or relabeled as checks against current `main`.

No candidate or historical auditor was executed during this refresh. No live
allocation, X11 action, physical input, or game run occurred. GitHub PR CI for
the refreshed rescue head and an independent PR review remain required before
merge; the original #7440/#7467/#7481/#7468 PRs and branches remain untouched.
