# Allocation 02 terminal disposition: STOP before batch 1

Issue #4304; allocation `inline-cache-uniqueness-4304-20260928-02`.

## First formal invocation

The published freeze and branch at launch were `0fd738cf066ca21e0e0341aeb557af582d1fe828`, based on current main `b556c109828e89b3a8e78cb618530a044c97d7d8`. The single frozen batch-0 command ran directly in local Arch Linux WSL2 with the 120-second timeout. No Docker CLI, GPU/CUDA, model, or remote execution was used.

```text
wsl.exe -d Archlinux -u root -- unshare --mount --propagation private -- timeout --signal=INT --kill-after=10s 120s /bin/sh /mnt/c/Users/junny/Documents/Codex/unjuno-x11-4304-v2/research/integration/inline_cache_global_uniqueness_4304_v2/src/run_private_x11.sh formal /mnt/c/Users/junny/Documents/Codex/unjuno-x11-4304-v2/research/integration/inline_cache_global_uniqueness_4304_v2/results/formal-02 0
```

The invocation exited 0 within the bound. `batch-0/BATCH.json` reports `COMPLETE`; all twelve planned first outcomes have `status=COMPLETE`. Each row records actor, policy, and Xvfb process exit 0, auth cleanup, and display socket/lock absence. These are runner receipts only; the frozen independent auditor and corruption controls were not run on an incomplete 24-case pair.

`BATCH.json` SHA-256: `a4df8f6cdef3ee864e1892f4debe9310f714c7a732ac3b9981dcd6b14bc36e9f`.
`INVOCATION.json` SHA-256: `20d4ef4ce5db6382de39fe7c9668757fba38a6293e42d4e92dcf9c351c464848`.
Per-case raw hashes are listed in `batch-0/BATCH.json`; raw image bytes, actor journals, exact requests/responses, process receipts, stderr, and cleanup fields remain unchanged beneath `batch-0/`.

## Gate failure and terminal decision

Immediately after batch 0, GitHub MCP readback observed `main` at `a924449f661d81bae88afc06fda5e0f3a41af673`, a different SHA from the freeze. That main commit is `fix(x11): refuse unsupported verification before input (#5230)`. The preregistered batch-1 gate requires current main to remain equal to the frozen base. Therefore **batch 1 was not invoked**. The allocation is consumed and terminates as `STOP_MAIN_ADVANCED_AFTER_BATCH0`: 12/24 sessions recorded, batch 1 0/12, reruns/replacements/exclusions/tuning 0.

No pairwise/scientific disposition is claimed. The 12 rows are not an audited formal result and must not be pooled with allocation 01 or a future successor. No retry, rebase-and-continue, replacement, or partial-result scoring is authorized by this freeze. Any follow-up requires a distinct fresh successor allocation with a new current-main freeze.

The original source freeze, all construction STOPs, batch-0 files, and this stop report are preserved. This file is deliberately outside `batch-0/`; the runner's batch-1 output-root guard now also refuses unexpected root contents.
