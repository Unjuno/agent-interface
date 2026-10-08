# Allocation 02 execution envelope

Allocation: `partial-multikey-recovery-2129-20260923-02`.

Scientific source, PLAN.md, H/T/D/C/U, 30-row schedule, comparison policies, application semantics, audit gates and corruption controls are byte-identical to allocation01's public freeze.

Changed factor only: the three already-defined 10-case batches are invoked in three **separate outer execution-tool calls**, instead of combining batch1 and batch2 in one outer call. This prevents the external 45-second envelope from being shared across two scientific batches.

Commands, each exactly once and stopping after a failed/incomplete batch:

1. `python3 runner.py formal 0 formal2/batch0`
2. `python3 runner.py formal 1 formal2/batch1`
3. `python3 runner.py formal 2 formal2/batch2`
4. after all three complete only: `python3 audit.py formal2`
5. after audit only: `python3 controls.py formal2`

No allocation01 row is copied or pooled. No source/gate/threshold changes. No consumed batch is rerun under allocation01 identity.
