# Actual assistant use of early effect delivery

The assistant launched interactive_v23 in a private Linux/X11 Calc session,
viewed initial `001.png`, submitted values 532/590 plus save, viewed modal
`007.png`, then submitted Return with finish_after. These were two assistant
decisions through the shared interface, not a script choosing GUI actions.
Both accepted programs completed with verified release; no rejection occurred.
The assistant received VERIFIED and independent success and sent finish cleanup.

The saved XLSX independently contains [532,590] and matches the effect's byte
digest. The audit verifies listed runtime source hashes, twelve exact AIT/PNG
observations, both output flush receipts and finalization retention. Decision
provenance remains caller-declared in runtime logs; actual viewing is additionally
recorded in this conversation's original-resolution image tool calls.

| Measurement | Value |
|---|---:|
| First public capture to early effect emit | 38.723 s |
| Modal terminal to confirmation admission | 15.899 s |
| Enter/save local program | 772.033 ms |
| Confirmation local program | 113.538 ms |
| Final terminal to early effect emit | 20.295 ms |
| Final terminal to independent evaluation emit | 31.847 ms |
| Accepted programs / clock requests / rejected commands | 2 / 2 / 0 |

Both effect and final evaluation appeared in the same `write_stdin` tool response.
Thus this run does not demonstrate the assistant making an earlier decision from
the early event. Runtime emit timestamps are not model receipt or comprehension
timestamps. The external tool output also contains PTY wrapping/escape sequences;
raw retained JSON is the authoritative runtime record. The large modal boundary
includes image inspection, clock round trip, model generation and tool dispatch;
it cannot be attributed to any one component from these logs.

This is a familiar known task with no matched baseline in this turn. It is not
proof of human-speed operation, general speedup, or token savings. Next evaluate
the event delivery boundary exposed to the assistant: compare equivalent live
tasks with an event-aware return mechanism, retaining final scoring and avoiding
polling or partial output that loses interrupts. Runtime micro-latency is no
longer the only bottleneck. No default promotion or freeze credit.

Evidence: `results/early-effect-self-use-01`; audit:
`audit_early_effect_self_use.py` and `results/early-effect-self-use-audit.json`.
