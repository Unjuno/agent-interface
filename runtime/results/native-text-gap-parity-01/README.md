# Native per-operation text gap integration

Live source: ceebc6ede. Fresh WSL/Xvfb LibreOffice Calc allocation, seed 991291.
The primary agent viewed the initial and both action images and chose each action.
No helper model, replay or action retry. Global text gap was 2 ms; explicit
per-operation gaps were 20 ms for A1=779 and 10 ms for A2=881. The agent handled
the observed XLSX format dialog, reviewed the resulting sheet and finished.
Saved XLSX readback: A1=779, A2=881. Recorded input waits: 20,20,10,10,250 ms
for the write/save program. Owner and SDK client both exited 0.

This validates pacing integration for one ordinary GUI task, not an optimal
gap, speedup, model-token reduction or general task-success rate. Requested
wait durations are not measured physical inter-keystroke timing. SDK stdio
was used; the registered desktop MCP host was not refreshed by this trial.
Local CI: 248 tests passed (176 protocol, 72 harness), recorded separately in
results-local/native-text-gap-parity-ci-01. Raw trial files and hashes are
retained here; verify.py checks archived bytes, saved cells and input waits
without starting an application or sending input.

Publication CI initially failed because the default-policy unit test imported
the GUI runner outside the CI sparse checkout. The unchanged pure policy was
moved into native_tail_v1 and imported by the runner and test; 248 local tests
passed again. This post-live refactor was not a second GUI trial.
