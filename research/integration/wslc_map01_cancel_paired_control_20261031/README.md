# WSLc MAP01 cancellation recovery: attack versus wait

This predeclared pair follows the earlier [single recovery trajectory](../wslc_map01_cancel_review_attack_20261031/). Both fresh allocations used Freedoom2 MAP01 skill 1, seed 991031 and the same runner: guarded navigation, observed A-key hold, cancellation and verified empty release, fresh review and refusal of the old alias. After five same-state engine frames, the control waited approximately 1,000 ms without input and the attack arm issued a guarded 1,000 ms F-key hold. Each then captured another fifteen frames. The fixed execution order was control `ab03` then attack `ab04`; one attempt per arm, no retries, no model.

| Arm | Kill counter before → after intervention | Object 14 labels after intervention |
|---|---|---|
| Wait control | 0 → 0 | Zombieman |
| Guarded attack | 0 → 1 | DeadZombieman |

Both cancellations reported an execution failure and verified empty input release, both reviews advanced the binding revision, both old aliases were refused without dispatch, and all subsequently dispatched actions and owner closes reported verified releases. Final tested keymaps were empty. Cancellation may have produced a partial turn: release does not imply no prior effect. `audit.py` verifies the retained runner hashes, event ordering, observations, frame hashes, action results and releases; `ab03.zip` and `ab04.zip` retain conditions, raw frames, labels, receipts and logs.

This is one sequential pair from a single seed, not a randomized or independent population estimate. The intervention intervals and observations are not exactly synchronized; simulation time continued and the simulator produced both labels and kill count. The attack was scripted, not selected by a model or tracker. This is evidence of a distinguishable simulator response in this pair, not proof of general causal performance, V39 planner retry in a game, model efficiency or MAP01 completion. WSLc used a private Xvfb, network none, 1 CPU, 1 GiB and a 30-second watchdog.
