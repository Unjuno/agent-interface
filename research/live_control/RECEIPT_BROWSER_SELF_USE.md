# Receipt-driven actual browser navigation and submission

The assistant used frozen socket v10 / interactive v26 with Chromium and the
existing local HTTP form fixture, seed 991025. It inspected the initial browser
image, navigated to the URL supplied by fixture readiness, inspected the newly
rendered form, then typed t991025 and submitted with Return. Both image views
used receipt_image.py references, parsed and passed to the original-resolution
viewer in the same functions orchestration. No DOM or output file was used to
choose inputs. The existing post-controller evaluator read the server's saved
request body only after final input admission had closed.

The form image showed a focused empty Value input. Its terminal observation
sequence was 10 and referenced 006.png, so neither the Calc sequence nor the
Calc filename was assumed. The assistant used that terminal's time plus 30 s
for a new bounded lease. The runtime admitted it before expiry. The initial
and navigation programs used ordinary admission and decision references.

| Metric | Measured |
|---|---:|
| First capture to independent evaluation socket return | 52.728 s |
| Initial socket return to navigation admission | 16.787 s |
| Form socket return to submission admission | 15.999 s |
| Navigation / submission local execution | 910.380 / 277.034 ms |
| Final terminal to independent evaluation emission | 12.786 ms |
| Evaluation emission to socket return | 12.501 ms |
| Programs / clock requests / socket calls before cleanup | 2 / 1 / 3 |

The server saved exactly value=t991025, independent evaluation succeeded, and
twelve decoded AIT frames matched their referenced PNG bytes. Two programs
completed with verified input release, no rejection, and a complete 21-record
received prefix. Accepted, terminal and evaluation share submission request
lineage. Cleanup completed and the runtime process exited with code zero.

This exposes a coverage distinction: early effect_evidence is currently wired
only for Calc. Chromium returns independent_evaluation and emits no early effect
record. A generic caller that waits exclusively for effect_evidence would wait
until timeout here despite successful completion. This trial explicitly requested
independent_evaluation. Do not fabricate VERIFIED evidence for an unsupported
adapter, or treat program completion as task completion. A shared caller needs
an explicit supported-outcome contract or a terminal-result fallback.

This is a simple existing desktop/browser fixture, not a new full benchmark
domain, a recovery trial, or representative web browsing. The assistant saw the
fixture implementation before use. No matched speed comparison with Calc is
valid: tasks and completion events differ. Outer intervals include model,
orchestration, transport and admission; model-only time and tokens are unmeasured.
No human-speed claim or architecture promotion follows. Next address the missing
shared completion contract and test a delayed/failed result rather than assuming
the fast successful server response is universal.

Evidence: results/receipt-browser-self-use-01 and
results/receipt-browser-self-use-audit.json. audit_receipt_browser_self_use.py
verifies source hashes, raw frame fidelity, saved request, release, lineage,
deadline and batch coverage. Transport/selector/audit hashes are retained.
