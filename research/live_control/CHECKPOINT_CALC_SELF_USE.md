# Actual Calc use of admission-preserving saved-cell checkpoints

The assistant used runtime v29/socket v14 and prepared caller v6 in the known
Calc fixture, seed 991031. It viewed the initial sheet, entered 612 and 129 in
A1/A2, saved, and received a terminal result plus a saved-cell checkpoint in the
same outer tool call. The explicit returned image reference 006.png (sequence 11)
showed the format dialog and the values in the live sheet.

The first checkpoint reported saved A1/A2 as null and status UNKNOWN, with reason
sample_mismatch_window_open. The displayed values were not treated as proof of
the saved artifact. The assistant viewed the dialog, confirmed the Excel format
with Return, then sampled again. The second checkpoint returned VERIFIED for
exactly A1=612/A2=129. Both queries retained task_success=null, attribution
not_established and observation_closed=false. Neither closed input admission.

Only after receiving that evidence did the assistant send explicit finish and
receive successful independent evaluation. This is the legacy finish path: final
scoring has no admitted-action attribution field. No such attribution is invented.
The final saved workbook is independently read and its bytes match the second
checkpoint hash. The first sampled workbook's bytes were not archived separately;
its reported null cells and hash cannot be independently replayed from a retained
pre-save artifact. The image and original query record are retained.

## Verification and timing

Twelve frames reconstruct exactly. Two programs are admitted and complete with
verified input release, no rejection, matching request lineage and assistant
producer declarations. All 27 delivered records are retained in order. The
runtime and every measured caller/query clock descriptor match explicitly. Query
IDs distinguish the two snapshots; neither renews observation or input authority.

| Interval | Before format confirmation | After confirmation |
|---|---:|---:|
| Query roundtrip | 16.233 ms | 17.030 ms |
| Verifier sample duration | 4.690 ms | 4.227 ms |

These wall intervals include local scheduling and are not CPU measurements or a
performance bound. Query clock identity is recorded before measuring send/receive.

The first checkpoint's return to the next prepared caller main took 27167.827 ms.
The VERIFIED query's return to explicit finish start took another 23352.712 ms.
First capture to VERIFIED query return was 76836.745 ms; first capture to final
score return was 100208.509 ms. There were six socket exchanges including finish.
This deliberately measures the extra outer boundaries rather than claiming the
few-millisecond verifier makes the whole interaction fast. No model receipt or
thinking interval, tokens/cost, matched speedup or human-tempo result is available.

Reports and original images were delivered together. Observation entries shown
to the assistant were reduced to event/sequence/image/context/semantic status,
with other records shown fully and all raw reports retained. This remains an
unvalidated presentation choice, not an established token optimization.

## Implication and next step

This is the first actual assistant checkpoint use and the first Calc integration
of the new query; the earlier browser checkpoint integration was scripted. It
demonstrates one scoped saved-output verifier across two artifact formats, not a
universal GUI effect contract or unseen recovery policy. Formula handling and
collateral workbook changes are not exercised by this run.

The 23-second verified-result-to-finish boundary is avoidable only if the caller
explicitly chooses an appropriate completion policy before execution. A future
conditional finish must validate the intended contract and query identity, preserve
UNKNOWN, and never equate an arbitrary VERIFIED field with whole-task success.
No automatic conditional finish or default promotion is introduced here.

Evidence: audit_checkpoint_calc_self_use.py and results/checkpoint-calc-self-use-01,
including source manifests, exact requests/replies, query clock descriptors,
client endpoint sidecars, images and the saved workbook.
