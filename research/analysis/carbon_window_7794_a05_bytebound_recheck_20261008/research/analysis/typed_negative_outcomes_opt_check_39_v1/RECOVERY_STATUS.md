# Recovery status — Issue #4990

This directory preserves the abandoned construction package from remote branch
`research/typed-negative-outcomes-opt-check-39-20260928` at tip
`36515aea96...`. The recovery PR is additive; it does not claim a completed
experiment or change Issue #4967's result.

## Evidence and disposition

- The original branch README and frozen protocol report formal local-container
  invocation count **0** and no result artifact. No formal runner, full
  corruption matrix, or container invocation was run during this recovery.
- The six original construction files were merged unchanged from the branch.
- `predecessor_contract.py` is an exact copy of the immutable predecessor input
  from `research/analysis/typed_negative_outcomes_successor_39_v1/contract.py`;
  its Git blob is `e9c447f02e6652369455959fe1b5f5dece31876e`.
- Local construction test: `python3 -B -m unittest -v test_preformal` — 6/6
  passed after restoring the missing predecessor input. This is not the frozen
  Docker allocation and does not constitute a formal result.

## Hold boundary

The original formal protocol remains unconsumed. Its source/input digest freeze,
read-back, and formal execution are incomplete. Do not infer PASS/FAIL, do not
reuse an output directory, and do not resume the old allocation from this
archive. Any future formal attempt must follow Issue #4990's Obstac constraints
and obtain a separately reviewed fresh allocation and freeze; the original
branch and Issue history remain the provenance record.
