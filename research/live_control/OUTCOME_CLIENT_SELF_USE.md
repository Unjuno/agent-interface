# Actual assistant use of the bounded outcome client

outcome_client.py connects to an existing private Unix socket and invokes the
candidate outcome_fallback_v2 policy once. It persists the full request/reply
transcript plus caller start/return timestamps to a new file, and prints the
interpreted result. It accepts no submit command. Its transport has a 35-second
socket timeout; the helper allows at most two exchanges, not a hard real-time
whole-call deadline. The output file is reserved before any query to avoid
performing network work when the path already exists.

The assistant started frozen socket v11 / runtime v27 with an xterm fixture,
seed 991028. It selected the initial image from the received reference and viewed
it at original resolution, then typed t991028 and Return. The submit call waited
for accepted. In the same functions orchestration, the new CLI then waited for
the result from that returned cursor. It returned evaluated=true using one
outcome read; no status fallback query was needed. The assistant read the result
before issuing finish. The process exited zero.

| Metric | Measured |
|---|---:|
| First image capture to outcome client return | 36.125 s |
| Initial socket return to input admission | 15.654 s |
| Local input program | 284.978 ms |
| Outcome client invocation wait | 81.423 ms |
| Terminal to independent evaluation emission | 11.735 ms |
| Submit / outcome reads / status queries | 1 / 1 / 0 |

Audit verifies the saved token, independent evaluation, admitted request lineage,
three exact AIT/PNG frames, input release, no duplicate submit and the complete
eleven-record received prefix. Input evidence is explicitly marked assistant.
The result was flushed before it was received. Model receipt timestamps and
actual token/cost measurements are unavailable.

This validates actual assistant use of the normal result path, not live fallback
or a pending-to-available status transition. It is a simple familiar fixture,
not a broad desktop benchmark. There is no matched A/B or human reference; the
short client wait must not be reported as total task latency. Most elapsed time
is still outside local input execution. Admission and outcome use two separate
socket exchanges in one orchestration here, so this is not evidence of fewer
transport round trips than combined send-and-wait.

Evidence: results/outcome-client-self-use-01 and
results/outcome-client-self-use-audit.json. Audit and client/transport/helper
source hashes are retained. Next validate live pending-to-available status
transitions using fresh query IDs, then use the resulting client in a case with
a real visible recovery decision. No default promotion or speedup claim.
