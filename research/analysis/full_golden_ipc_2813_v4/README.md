# Task-1 successor v4

Successor to v3 after the current model backend restored the public `call`
boundary. It reuses the v3 historical-route wrapper without retrying v3 and
pins the current dependency snapshot. This gate and allocation remain task-1
only; no authority is granted by the entry check.
