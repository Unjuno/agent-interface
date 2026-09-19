# Golden v3 adapter P2 rebase successor to #2360

This additive successor starts from current main and addresses the review findings
on #2360 without modifying that historical PR.

It adds a regression fixture for nested runtime_failed: current main must retain
it as partial with partial effects and diagnostics, while nested refused remains
a refusal. It also verifies completion/task-success separation, cleanup failure,
unknown status fail-closed behavior, and zero authority/model/GUI/input/network
calls.

This is a scoped adapter contract result. It makes no live desktop, model, GUI,
input, network, latency, token, or general task-success claim.

Reproduction:

    python audit.py
