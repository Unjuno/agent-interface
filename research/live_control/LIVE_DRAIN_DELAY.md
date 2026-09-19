# Integrated final drain while evaluation remains gated

The prior actual Calc run collected a ready final result within the confirmation
CLI, but its delayed path had only injected-exchange coverage. This probe executes
the complete prepared_exchange CLI against socket v11/runtime v27 with ordinary
private X11 Calc input and a test-only evaluator gate.

After entry/save, the confirmation emits early saved-cell evidence. Independent
evaluation cannot run until the probe releases a file gate. The CLI performs its
one zero-server-wait drain, receives timeout, and returns effect_observed with
task_success unset and a final-only continuation. The probe verifies that the
gate is still closed, the runtime is live and no evaluation event has been emitted
after the CLI subprocess has returned. Only then does it release the gate and
read the final successful evaluation through that continuation, without input
resubmission.

prepared_exchange_v3 adds --producer (assistant/scripted/human) so this automated
test explicitly records scripted input. This changes attribution metadata only;
the drain and runtime behavior are unchanged. Earlier measured versions remain
frozen. The producer label is caller-declared, not independent proof of viewing.

| Check | Result |
|---|---|
| CLI returns before evaluator gate release | yes |
| Early task success | unset |
| Final evaluation after release | true |
| Accepted programs | 2 |
| Exact AIT/PNG frames | 12 |
| Drain server wait | 0 |

Early socket return to processing end was 32.789 ms. The harness released the
gate 18.929 ms after that processing endpoint, after the CLI process returned.
These are injected-test timings, not model receipt or natural task-latency data.
Audit verifies saved cells [612,129], workbook hash, both input releases, scripted
evidence labels, source hashes, matching early/final lineage and the full received
prefix. Both the client and runtime exit zero and the socket is removed.

This establishes that the integrated CLI does not wait for a deliberately gated
evaluator when its socket remains responsive. It does not establish a hard wall
time bound during blocked connection/read, permanent process stalls, broken output
publication or scheduler overload. The socket still has its 35-second I/O timeout.
No input is replayed when the drain returns pending. All early, tail and final
records remain in artifacts. The test does not measure human speed or tokens.

Evidence: results/live-drain-delay-01 and probe_live_drain_delay.py, with frozen
gate wrappers and candidate prepared_exchange_v3.py in the source manifest.
The ready path has actual assistant evidence; the delayed path now has integrated
scripted evidence. Next assess transport-fault behavior and compare caller boundary
counts across a non-Calc task before recommending this optional mode generally.
