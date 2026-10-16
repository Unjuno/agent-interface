# Allocation 05 queue correction

Allocation 05 already STOPped before the runner because its main freeze was
stale. A queue refresh also found a five-minute overlap with #5550's requested
2026-09-30 17:15–17:30 UTC interval. The original proposed 17:05–17:20 window
was therefore invalid and is withdrawn. No Docker container or X11 input ran;
Allocation 05 remains consumed and must not be retried. The original
`STOP.json` is preserved unchanged; this correction is additive.

Evidence: [#5085 correction comment](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5916071403).
