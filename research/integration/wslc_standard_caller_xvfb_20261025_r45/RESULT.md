# R45 — WSLc 3.86 s pause under a 4 s transaction deadline

**Disposition: `PASS_SCOPED_4S_TRANSACTION_3860MS` (26/26 evidence checks).** The unchanged public standard-caller test passed in a digest-pinned, network-disabled Ubuntu container. Xvfb paused for 3860.372 ms and resumed through its retained pidfd. Supervisor release/readback completed 20.877 ms before the transaction deadline; a separate parent readback arrived at +4104.230 ms, and the late-event horizon and both synthetic task oracles passed. Runtime cancellation custody remained UNKNOWN, replay denied, and task success null. The Xvfb process and exact container were removed.

This is one synthetic-Xvfb boundary sample between R43's 3,850 ms pass and R44's 3,875 ms deadline failure. It is not a reliability estimate or evidence of Windows desktop, MAP01, real-app transfer, or matched efficiency.
