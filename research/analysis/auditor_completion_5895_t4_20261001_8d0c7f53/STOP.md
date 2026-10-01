# T4 terminal STOP — candidate container was not created

Allocation: `AUDIT-COMPLETION-5895-T4-ORBSTACK-20261001-01-8d0c7f53`  
Owner: Codex thread `01a0b98b-8d0c-7f53-92bc-4c6a28d73c73`  
Observed: 2026-10-01 10:33:50 UTC (slot 10:30–10:50 UTC)

## Outcome

`STOP_BEFORE_CANDIDATE / NOT_EVALUATED`. The single candidate `docker run` wrapper invocation returned exit 125 before Docker created a container. The `--mount` argument for `/out` used `rw` instead of Docker's required key/value syntax (`readonly` is a flag; writable is the default). The shell also could not create the requested CID file because the receipts directory had not been created. Docker's stderr reports the invalid mount field. No candidate script, target CLI case, or independent auditor ran; no scientific outcome is inferred. The one-shot allocation forbids retry, so this invocation is terminal.

## Preserved receipts

- `results/formal-t4-01/receipts/candidate.exit`: `125`
- `results/formal-t4-01/receipts/candidate.stdout.txt`: empty
- `results/formal-t4-01/receipts/candidate.stderr.txt`: shell redirection and Docker argument diagnostics
- `results/formal-t4-01/receipts/candidate.cid`: not created
- `results/formal-t4-01/receipts/candidate.inspect.json`: empty; no container ID existed to inspect
- `results/formal-t4-01/output/`: remains empty

The exact source identities, owner, host, allocation, image and pinned platform passed their observed preflight checks. The candidate launch plumbing did not pass. No other containers were stopped, removed, or modified. The frozen PR #5630 source and T3 evidence remain unchanged.

## Exact failed invocation

The allocated command's final bind argument was `--mount type=bind,src=<empty output path>,dst=/out,rw`. Docker rejected `rw` as a field without a value. The command also directed `--cidfile` into a receipts directory that did not exist at launch. These are harness construction errors, not target/auditor behavior. No corrected command is run under this allocation.

## Next step

Report this terminal STOP on Issues #5895 and #5085. Any corrected successor requires a new allocation and a fresh start gate; it must create and validate the receipts directory and use a valid writable mount before the one-shot candidate command.
