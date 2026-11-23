# Calc effect-verification receipt-window order — current-main R02

**Frozen main:** 5156ec0e018168dac7691ffe31e13829eecf44f4
**Checkout:** clean detached worktree at the frozen main commit.
**Scope:** local synthetic artifact and receipt-construction tests only.
**No:** GUI/app launch, provider, Docker, WSLc, formal allocation, or live task.
**Command normal:** `python -m unittest runtime.guarded_x11_v1.test_calc_task_artifact_v1`
**Command optimized:** `python -O -m unittest runtime.guarded_x11_v1.test_calc_task_artifact_v1`
**Acceptance:** unchanged 20-test suite passes in both modes; retain both streams, exits, timestamps and these hashes.

## Frozen source SHA-256
9538aa01b834c1d9a80a097ae99f2053131b7c5187068aa670355adeb247d81e  runtime/guarded_x11_v1/calc_task_artifact_v1.py
d2e4573e0761df31603354b22ce7c5e07d6b7a6cf0f0c0448710919c94304855  runtime/guarded_x11_v1/test_calc_task_artifact_v1.py
19c70cd9da719536cfb6911ade0b6119fbb2d61898e178669864c87b3c531f30  runtime/guarded_x11_v1/calc_effect_v1.py
8f3b7cdd14620837aaa444916662a09201693965dae61115abc2ab5a0eba9aa9  runtime/guarded_x11_v1/calc_profile_v1.py
54756c4a4918331efb4506dfd185ff7e738b4f3a01a89c731a2e3ae823f99bd3  runtime/guarded_x11_v1/process_identity.py
5096414d131116662d2cf3ae6039ac275e9304b32807d1236ac1cc6731d35464  runtime/guarded_x11_v1/calc_symbolic_plan_v1.py
36e085a910ba8731a85e4ccf899d0fa7c6e6e0de1a98eebd0e647f1330ebc3c8  runtime/guarded_x11_v1/test_calc_symbolic_plan_v1.py
fe66297f57aa012dbe79f668076f906f015491dfbe6a1c83002f5213f3003367  runtime/core_v1/compiled_gui.py
