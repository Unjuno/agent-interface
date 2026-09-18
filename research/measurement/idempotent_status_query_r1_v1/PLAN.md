# #24 status-before-retry rung
Task: IDEMPOTENT-STATUS-QUERY-R1-20260918-001
Base: ae7ddd5c2517c00b6a6187db7f1db04555dc00e4
Parent: #24; evidence parent #1469 / PR #1479
Factor: recovery policy after an ordinary receipt is missing at timeout.
Formal: seed 240120260918001, 160000 paired traces, one invocation, reruns/replacements/tuning 0.
Decision: PASS only if status-before-retry has no unsafe replay or duplicate non-idempotent effect, preserves eligible retries, independent oracle agrees exactly, and integrity controls pass.
Scope: standard-library synthetic ledger only; no GUI/X11/model/provider/network/task input/shared runtime.
