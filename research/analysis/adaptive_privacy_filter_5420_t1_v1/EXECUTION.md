# Execution record

One formal simulator invocation completed on 2026-09-30 in OrbStack Docker 29.4.0 (`linux/aarch64`), with the image and exact command in [PLAN.md](PLAN.md). Container network was disabled; root filesystem and source mount were read-only; CPU=1, memory=256 MiB, pids=64, all capabilities dropped, and no-new-privileges enabled. Only `raw/formal/` was writable.

The frozen experiment exited 0 and retained 4,096 inputs / 20,480 policy rows. The independently implemented auditor ran once on those bytes, exited 0 with `PASS_RAW_AUDIT`, `errors=[]`, and rejected 4/4 corruption controls. Neither experiment nor auditor was retried. No live application, GUI input, model, or external network was used.

The simulator samples only the explicitly declared randomized-response channels. Its observed accuracy numbers are finite seeded corpus measurements; the mechanism-level epsilon bound follows from the declared channel/composition contract, not from the empirical accuracy estimate.
