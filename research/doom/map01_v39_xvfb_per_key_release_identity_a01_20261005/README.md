# MAP01 v39 Xvfb per-key release identity A01

This package tests the PR #7717 retained-input backend against a real local
Xvfb server. It covers repeated same-key cycles and a two-key hold released in
the opposite order from admission. The candidate records the backend receipts,
server keymap after every edge, and the focused client's dispatched key events;
the auditor reconstructs the expected sequence independently from raw JSON.

The exact source snapshot, candidate, decision gate, and no-retry rule are
frozen in `FREEZE.json` before the sole candidate invocation. Setup is limited
to the private network-isolated VM, Xvfb, and Python Xlib. There is no Doom,
ViZDoom, model, GPU, physical input, network workload, or GUI application.

The runner writes first-outcome evidence to `results/A01/`; setup and source
identity are retained separately. This construction result concerns only
owner/backend receipt correlation and Xvfb client event dispatch. It cannot
close Issue #59's corrected threat-exposure gate or the separately labelled
MAP01 attempt.
