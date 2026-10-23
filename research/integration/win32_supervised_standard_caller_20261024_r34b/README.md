# R34 — dense held-callback polling and distinct recovery hook event

R33 demonstrated that the fixture was actually Q-down before cancellation and that an independent same-generation read observed Q-up while the recovery callback remained blocked. It fell short of its frozen gate by one public poll (20/21) and retained no second post-release Q-up hook event.

R34 preserves the one-fixture, one-dispatch, one-cancel R33 design. It reduces only the inter-poll delay during the 1250 ms callback hold to 10 ms and waits after release for a second injected Q-up callback whose entry follows the first callback return. The auditor requires at least 21 same-call hold polls and separately checks the distinct second callback. All waits remain finite.

Task effect remains an independently observed pre-cancel click/save, not post-recovery success; runtime `task_success` remains null. No MAP01, WSLc, efficiency, reliability, or kernel-causality claim is made.
