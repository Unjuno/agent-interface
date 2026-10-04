# #5156 synthetic completion-sentinel terminality probe

This host-only probe tests whether the retained T3 raw-only auditor enforces that its one successful runner completion record is the final JSONL row. It uses the exact T3 CLI and fixture source frozen at main f474970f82d68b6648aac64f99048ad0c2fd5732.

The audit accepted both the positive control, whose integer-zero completion record is last, and a matched treatment where that same record is first. The 25-row inputs have identical record multisets and identical non-completion row order. The independent raw-only audit verified the source, row-order mutation, CLI streams/results, hashes, and exit/status agreement.

See the full [report](REPORT.md), [preregistration](PREREG.md), and [raw outputs](results/formal-01/). This is synthetic CLI evidence only. It did not exercise Docker, X11, physical input, MAP01, application effects, formal host-receipt mode, latency, or product behavior.
