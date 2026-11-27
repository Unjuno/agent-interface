# Calc effect-verification receipt-window order — R02 result

**Disposition:** `PASS_LOCAL_SYNTHETIC_CONTRACT`

**Frozen main:** `5156ec0e018168dac7691ffe31e13829eecf44f4`; the test ran from a clean detached worktree at this exact commit.

**Runtime and result:** Windows CPython 3.11.9. `runtime.guarded_x11_v1.test_calc_task_artifact_v1` passed 20/20 normally and 20/20 under `-O`; both exits were 0. Full stdout, stderr, and UTC timestamps are retained.

**Finding:** the parent-held registered Calc Save receipt accepts the save-request timestamp inside the effect-verifier interval, and rejects the before-start and after-acceptance cases. The test also preserves the distinction between parsed artifact contents and a trusted GUI/save lifecycle receipt.

**Scope limit:** synthetic receipt and artifact tests only. No Calc GUI/process, input, provider, Docker, WSLc, formal allocation, or live task ran. This does not prove second-domain live task success, repeated recovery, or matched efficiency and does not close #57.

**Earlier setup correction:** R01 was first run from a stale worktree. Its receipt module, test, and directly read Calc helpers matched main, but `runtime/core_v1/compiled_gui.py` did not. R01 is excluded from the current-main result because of that dependency mismatch. R02 reran the same unchanged suite from the exact main worktree and is the qualified result.

\n