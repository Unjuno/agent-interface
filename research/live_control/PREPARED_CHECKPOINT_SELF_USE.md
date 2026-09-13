# Actual assistant use of the prepared checkpoint caller

prepared_checkpoint.py composes prepared_exchange_v6 terminal execution with the
explicit checkpoint_finish policy. The caller must provide --finish-on-match and
a contract file. Contract shape is validated with a no-I/O callback before GUI
input. The request remains explicit steps and ordinary runtime admission. Only a
completed program enters the checkpoint policy; rejected or unresolved programs
do not automatically trigger a checkpoint or finalization.

```sh
python3 research/live_control/prepared_checkpoint.py SOCKET BATCH RUN_DIRECTORY \
  PROGRAM_ID STEPS_JSON CONTRACT_JSON --lease-ms 30000 --finish-on-match --out NEW_DIR
```

Use runtime v31/socket v16 for scoped explicit-finish evaluation. Default producer
is assistant; scripted probes must specify --producer scripted. The selected saved
contract is the caller's explicit closure policy, not a general task success test.

The wrapper preserves the prepared caller's stdout/stderr and report, policy
requests before sending, replies, call timestamps and the final report. Policy
I/O uses an absolute deadline of server timeout plus one second, at most 31 seconds.
The prepared subprocess has a 40-second parent timeout, but file operations,
report parsing, output flushing and the overall wrapper have no hard deadline.
After transport failures, inspect persisted requests; a fresh invocation is not
an exactly-once retry. No automatic input replay is implemented.

For needs_decision with boundary replies, continuation-batch.json combines the
program and query records and their cursor for an explicitly chosen next program.
It is not authority or proof of semantic validity. The generic helper also uses
needs_decision for malformed/mismatched evidence; callers must inspect those
records rather than blindly treating every continuation file as a valid snapshot.
No continuation file is produced after final evaluation or a transport gap/error.
The returned image is the program's historical reference, not a new post-evaluation
capture. All records are retained even when the displayed observation metadata is
reduced for this particular experiment.

## Actual use

The assistant viewed initial Calc image 001.png, entered 612/129 and requested
save. The first wrapper call returned needs_decision, task_success=null and the
format dialog reference 006.png (sequence 11). Its saved-cell checkpoint was
UNKNOWN; no finish was attempted. The assistant viewed the modal, chose Return
to confirm Excel format and used the continuation batch for the second call.

That call completed the input program, archived and verified the saved cells,
sent the explicitly selected finish request, and returned independent success.
The assistant did not need another model/tool turn merely to request final scoring.
Both policy exchanges still occur, and the model still inspects the modal before
choosing confirmation. The process exits normally after the scoped finish.

Twelve frames reconstruct exactly; two programs complete with verified release,
no rejection and matching request lineage. All 27 delivered records and persisted
policy requests/replies match. The final score is correlated to its finish request,
and its saved workbook matches the checkpoint hash. Both UNKNOWN and VERIFIED
archived states replay after the source directory is deleted. Runtime, prepared
caller and wrapper clocks have identical descriptors.

| Observed interval | Duration |
|---|---:|
| VERIFIED reply received to finish-call start | 4.037 ms |
| Modal report ready to confirmation wrapper main | 18208.077 ms |
| Initial capture to final score reply | 82346.185 ms |
| Initial capture to wrapper processing end | 82351.022 ms |

The first interval includes writing the received reply before the policy continues.
The earlier explicit assistant finish required another outer turn and 23.353 seconds
after the verified reply. These sequential runs differ in preparation/orchestration,
runtime and storage behavior; they are not a matched causal speedup study. The
current initial-capture total also includes roughly 39 seconds before the initial
clock request, including preparation performed during the session. Model receipt,
thinking time, actual token cost and human tempo remain unmeasured. The remaining
18-second visual decision boundary is still far from the full goal.

Evidence: audit_prepared_checkpoint_self_use.py and
results/prepared-checkpoint-self-use-01 with source manifests, requests, replies,
clock descriptors, images and archived workbook versions. Keep the caller optional;
its exception/timeout paths and broader application contracts need further coverage.
