# Formal allocation 001 — STOP

This is the single preregistered seed-2001 attempt. It is retained as STOP and was not retried.

- Freeze commit inspected on GitHub: `23372fc80ce5e3006f1c5464feeaca25fbabff36` (source parent `da083bc6eea8f59e367008ca67d5047da5008f09`).
- Frozen evaluator/controller images: `sha256:1381f1d3522c69e011e62340167497b02b3b5e81bc4d719641f7e3b34b905ecd` / `sha256:4a800a24ca4ed4e8249cf35559b37ffca7e23a8cd76e7df1434fe4622e22d389`.
- Run: 2026-09-27 02:46:13–02:46:20 UTC; seed 2001, difficulty 1.0, fixed clock.
- Terminal status: `STOP — evaluator report unavailable before container exit`.

The controller returned exit 0, its X11 probe returned exit 0, and a 1,923,179-byte XWD was retained. The posthoc audit confirms that this capture matches the probe hash; the controller process list exposed only its probe, its tested source/report paths were inaccessible, the evaluator PID 1 command line contained seed 2001, and the Docker network was internal. This does **not** verify that the evaluator received the key event or naturally recorded `deadline_miss`: `/evidence/report.json` and the evaluator's post-run logs/inspection were lost with the evaluator container's short-lived tmpfs before collection.

The retained runner used `--autoclose 0.5`. The likely mechanism is a collection race against shutdown, but no evaluator report exists to establish the exact point at which the file disappeared. Do not infer a PASS, failure-locus result, or task outcome. The initial frozen auditor also crashed while parsing Docker inspect's top-level JSON array; `POSTHOC_AUDIT.json` was produced by a separate read-only, network-disabled auditor and deliberately retains the STOP disposition.

No formal retry is permitted for allocation 001. A later experiment requires a distinct successor allocation, fresh preregistration/freeze, durable host-side result collection, and a separately reviewed auditor.
