# Cancellation while an artifact checkpoint waits

The optional v29 runtime/v14 socket candidate was exercised in a real private
Linux/X11 Chromium session. A test-only wrapper gates the artifact verifier before
it reads the file. Input execution and cancellation code are unchanged.

The probe starts a checkpoint, confirms the verifier has entered its gate, and
issues another checkpoint. The second query returns UNKNOWN/verifier_busy rather
than queuing. It then admits a four-second Right-key hold, observes its step-start
event, waits 100 ms and sends cancel through the separate cancel socket.

The cancel response reports matched=true and a subsequent terminal reports
cancelled with verified input release. Only after receiving that terminal does
the probe release the verifier gate. The delayed checkpoint then returns UNKNOWN
for the absent artifact, with task_success=null and the original query identity.
The process remains live until explicit cleanup, then exits successfully.

This establishes that this sleeping verifier does not prevent cancellation and
release in this run. The physical key-down instant was not independently sampled;
the evidence includes an admitted hold, step-start, cancellation match and verified
release. It does not establish a hard bound, CPU/GIL contention behavior, blocked
stdout behavior, permanently stuck worker shutdown or a completed browser task.

## Timing and audit qualification

The cancel request roundtrip was 34.219 ms, measured between timestamps in the
same probe process. It is one sample without a no-verifier baseline. The raw probe
also computed cancel-start to runtime terminal as 33.826 ms, but did not record
the parent process clock descriptor. The audit therefore explicitly rejects that
cross-process number as an established interval and records null with missingness.
No clock identity is retroactively inferred. Cancellation preceding verifier gate
release is proven by the probe's sequential operations and received terminal.

The audit checks the complete 17-record received prefix, both exact reconstructed
frames, and runtime dependency hashes. Owner records include verified cancellation
release. The absent artifact's UNKNOWN does not become success during the wait.
Cleanup's ordinary task evaluation is unrelated to this cancellation control;
the probe never attempts the form task.

Evidence: probe_checkpoint_cancel.py, audit_checkpoint_cancel.py and
results/checkpoint-cancel-01. The wrappers gated_checkpoint_entry.py and
gated_checkpoint_socket_entry.py freeze the injected verifier wait separately.
The candidate remains optional. Actual assistant checkpoint use, Calc integration,
and CPU/output contention controls remain open.
