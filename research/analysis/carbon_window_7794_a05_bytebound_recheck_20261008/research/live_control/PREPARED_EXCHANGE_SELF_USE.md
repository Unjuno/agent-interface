# One command for preparation, send and outcome wait

prepared_exchange.py combines received-evidence program preparation with a
single request-scoped send/wait socket exchange. The assistant supplies explicit
steps, program ID, lease duration and terminal/outcome boundary. Outcome mode
sets finish_after; terminal mode leaves further decisions possible. It reserves
a new artifact directory and saves preparation and the exact request before
connecting, then saves the raw reply and report. All received records remain
available. Image lookup errors are separate from the already-received result.

No input retry occurs on errors. The persisted request ID is the one associated
with an uncertain write; creating a new invocation is not a recovery protocol.
The CLI provides neither automatic status fallback nor restart-safe replay.
Outcome continuations can use the existing read-only client; terminal results
are program status, not task success. An existing output directory stops work
before network activity. File writes are not fsynced or atomic durable journals.

The assistant used it in private X11 xterm with the same seed 991030 and exact
text/Return steps as prepared-self-use-01. It viewed the received initial image,
then issued the combined command and inspected evaluated=true before cleanup.
The saved token is correct, three frames are exact, input release is verified,
the eleven-record prefix is complete, and the program has one submit and no
rejection. The runtime exited zero. Goal and step equality are checked by audit.

| Metric | Combined caller |
|---|---:|
| First capture to socket return | 27.448 s |
| Initial socket return to admission | 13.097 s |
| Local input program | 264.670 ms |
| Combined send/wait socket exchange | 312.632 ms |

The preceding split caller used two socket exchanges for submit/admission and
outcome; this invocation uses one. Its first-capture-to-client-return was 36.649 s.
The new measurement stops at socket return, before local report/image processing;
it is not the model's receipt time. The shorter interval is an observed sequential
result, not a causal speedup estimate. Each variant has one familiar run and
uncontrolled outer tool/model delays. No human comparison or actual token/cost
measurement exists. The full record report deliberately does not claim compact
model input; callers must not drop interrupts merely to reduce printed text.

This change makes actual invocation shorter and restores combined send/wait
while preserving evidence preparation. It does not solve the remaining seconds
of outer decision delay. Terminal-mode self-use, transport-failure recovery and
multi-step visible correction with this CLI remain unverified. Next use it in
a branching GUI case rather than repeatedly measuring this known token task.

Evidence: results/prepared-exchange-self-use-01 and
results/prepared-exchange-self-use-audit.json. Runtime/client source manifests,
exact request, preparation, reply, report, images and saved token are retained.
No default promotion.
