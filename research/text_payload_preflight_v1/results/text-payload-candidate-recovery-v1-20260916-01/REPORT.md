# Whole-payload preflight: retained candidate-only X11 result

## Disposition

**PASS_SCOPED_PAYLOAD_PREFLIGHT / HOLD_COMPARATIVE_AND_OFFICE_PROMOTION**.

Source freeze: e1a0c6a7a3f23f36ac9bac011a4338586c082772.
Result ID: text-payload-candidate-recovery-v1-20260916-01.
Executed once after source freeze; no GUI rerun. The runner enforces the three original dependency Git blob IDs. Its own readback blob 3239789a8bc2cffa137454142d910d6158dcc86b matched the local file before execution.

## Measured result

| Gate | Retained result |
|---|---:|
| Unit tests | 13/13 PASS |
| Printable ASCII payloads delivered exactly | 95/95 |
| ASCII control-character payloads rejected before any input | 33/33 |
| Stale observation, stale binding, expired lease, wrong focus | 4/4 zero-input refusals |
| Clipboard owner + UTF-8 text and X keymap hash unchanged during text attempt | 132/132 |
| Physical keymap reports no held key; pointer button/modifier mask zero | 132/132 |
| Complete uniquely identified raw trial rows | 132 |

Each code-point payload is `office` + one ASCII code point + `tail`. The supported cases are U+0020..U+007E. The other 33 ASCII code points are refused, not interpreted as editing commands. For example `office_tail` and `office!tail` are delivered exactly; `office` followed by newline and `tail` is refused with zero emissions and no receiver text/events.

This validates one compiled-before-input text plan, not a universal ASCII/Unicode route. The candidate reads the live first-group two-level keymap, pre-resolves every character including required Shift, binds the map hash, and rejects an unrepresentable full payload before the first key. No clipboard fallback or global-keymap remapping is used. Initial clipboard content is deliberately set by the fixture before each measured environment, not by the delivery candidate.

## Conditions and limits

Python 3.13.5 / GCC 14.2.0, Linux 6.18.44 x86_64 glibc 2.41, AMD EPYC 9V74 80-Core Processor, CPU affinity [0,1,2,3,4], python-Xlib module version (0,15), authenticated xvfb-run/Xvfb 1024x768x24, Openbox, separate-process Tk input consumer. Requested pacing is 0.012 s (12 ms) after each character; CPU clock was not controlled. This is a finite conformance matrix, not a timing benchmark or a population reliability estimate. No model/provider request was made.

The receiver is a real separate GUI process. Reset/scoring IPC belongs only to the fixture, not to the agent input route. Observation/revision numbers are supplied snapshots, not measured grounding freshness. Only initial modifier/held-input neutrality and the specified context controls are tested. Midflight environmental changes, server disconnect, hard process death, alternate XKB groups, arbitrary Office behavior, three-OS support, Unicode/IME and token efficiency remain unproven. Text execution is NOT an atomic transaction and does not roll back a prefix after a midflight failure.

## Evidence loss is not a pass

Before this recovery allocation, the original plan at 22bbaeba28016deda3efb201fe5222ea26dd6fb0 had development probes and six development Writer sessions. Their raw logs/documents disappeared with the disposable workspace. Those runs remain described only by DEVELOPMENT.md and conversation tool output; they are NOT promoted as retained formal evidence.

The original 260-trial baseline comparison and six-session formal Writer transfer never started. The original launch helper stopped during missing package-metadata collection, then the workspace disappeared. RECOVERY.md freezes this narrower candidate-only allocation separately. This result is neither a replacement baseline comparison nor a reconstructed Writer outcome.

During publication the original source branch was no longer present (update_ref returned 422 Reference does not exist); no cause or other-agent ownership is inferred. The same immutable commits were retained on a new branch, without force-pushing or rewriting main.

## Readback audit and integration decision

All 132 original rows were re-read; IDs and order checked; supported exactness, zero-effect refusals, clipboard/map equality and empty physical state recomputed. A fresh ZIP read verified all 13 entries covered by the delivery archive's manifest. This was same-session readback, NOT an independent reviewer approval.

The exact full raw JSONL is published in three base64 parts (gzip), with its original SHA-256 and decoder instructions in PUBLICATION.json. Unit log and environment/source receipt are also published. No lost development files are fabricated. A first attempted single-string raw upload failed its Git-blob identity check and is unreferenced; only the three independently hash-matched parts are retained in this result tree.

Integration recommendation: keep this candidate isolated and replace coarse coverage claims with concrete payload/keymap preflight before runtime dispatch. An exception after writing a prefix is not permission to redispatch the whole text via another route: that could duplicate content. Do not claim comparative superiority or Office support from this candidate-only result; independent review and the originally proposed durable Office/baseline comparison remain separate gates.
