# R46 — WSLc 3.86 s pause under a 4 s transaction deadline

**Disposition: `PASS_SCOPED_4S_TRANSACTION_3860MS_REPLICATE` (27/27 evidence checks).** The unchanged public standard-caller test passed in a digest-pinned, network-disabled Ubuntu container. Xvfb paused for 3860.287 ms and resumed through its retained pidfd. Supervisor release/readback completed 18.848 ms before the transaction deadline; a separate parent readback arrived at +4108.282 ms, and the late-event horizon and both synthetic task oracles passed. Runtime cancellation custody remained UNKNOWN, replay denied, and task success null. The Xvfb process and exact container were removed.

This is an independent exact-condition replication of R45 on synthetic Xvfb. It does not establish a timeout threshold, reliability estimate, Windows desktop/MAP01 behavior, real-app transfer, or matched efficiency.
