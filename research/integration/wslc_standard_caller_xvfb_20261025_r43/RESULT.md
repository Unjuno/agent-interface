# R43 — WSLc 3.85 s pause under a 4 s transaction deadline

**Disposition: `PASS_SCOPED_4S_TRANSACTION_3850MS` (26/26 evidence checks).** The unchanged public standard-caller test ran once in a digest-pinned, network-disabled Ubuntu container. Xvfb paused for 3850.292 ms and resumed through its retained pidfd. The public cancel response took 311.117 ms; the transaction elapsed 3979.459 ms against its exact 4,000 ms deadline.

The independent supervisor release/readback completed 27.552 ms before the transaction deadline; a separate parent readback arrived at +4071.340 ms, and the +8504.180 ms horizon found all keys up with no delayed `b`. Both old and fresh synthetic task oracles passed. Runtime cancellation custody nevertheless remains `UNKNOWN`, with `release_confirmed=false`, replay denied, and `task_success=null`. The Xvfb process and exact container were removed. See this packet for the preregistration, raw caller output and audit.

## Scope

This is one synthetic-Xvfb boundary sample between R40/R41's 3,800 ms passes and R42's 3,900 ms deadline failure. It is not a reliability estimate or evidence of Windows desktop, MAP01, real-app transfer, or matched efficiency.
