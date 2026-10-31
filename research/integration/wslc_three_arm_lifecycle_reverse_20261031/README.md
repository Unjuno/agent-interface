# WSLc Chromium: reverse-order lifecycle replication

This is a prospectively frozen reverse-order successor to `wslc_three_arm_lifecycle_20261031`: ephemeral → persistent → plain instead of plain → persistent → ephemeral. Each arm has a fresh model session and WSLc container, one independently validated schema preflight, six tasks, fixture scoring and cleanup. The same pinned harness/source manifests, image, seed, requested `gpt-6.1-sol low`, CPU/memory, timer boundaries and recorded host executable hashes were used. The main SHA is an integration reference; the mounted source is the earlier retained snapshot, not asserted identical to current main.

| Order | Plain lifecycle | Persistent lifecycle | Ephemeral lifecycle | Plain vs persistent input tokens |
| --- | ---: | ---: | ---: | ---: |
| forward | 42.731 s | 34.672 s | 43.408 s | 104,105 vs 36,859 |
| reverse | 42.603 s | 34.331 s | 47.434 s | 104,025 vs 36,859 |

Persistent was 18.86% and 19.42% shorter than plain within the defined host-clock lifecycle in these two pairs. The two-run medians are 42.667 s plain and 34.502 s persistent; with two observations they are descriptive midpoints, not a population estimate. Each arm had 6/6 exact fixture submissions. All recorded terminal releases were neutral: 18 plain, 57 persistent and 48 ephemeral per block. Persistent used one preflight plus two task model calls; each other arm used one plus six. Cached tokens are included in input, not additional; provider cost is unknown.

The timer starts immediately before starting the host process and ends after both host and WSLc container exit. It includes preflight, validation, container/app startup, task execution, scoring, process cleanup, orchestration polling and timing writes. It excludes launcher imports/startup, source preparation/hash checks, image build/pull, post-run audit/archive and any outside wait. Post-run WSLc listing reported no remaining named containers. Complete boundaries and caveats are in the predecessor report.

Two executions of one fixed-seed fixture are not independent randomized trials. Reversing outer order changes plain and ephemeral positions, but **persistent stays second in both**; it does not remove all order, cache, workload or provider confounding. Failure/recovery parity across methods and current-main production integration remain unproved. These figures support only a scoped comparison, not general speed, cost, reliability, human-tempo or MAP01 completion claims.

`public.zip` retains frozen harness manifests, screenshots, preflight responses, model call outputs/usage, fixture histories, runtime events, timers and cleanup summary. The omitted source trees were hash-checked before and after, with recorded manifests; private protocol/workspaces are hash-indexed. `python audit.py` checks this run; `python compare.py` runs both this and the sibling predecessor audit, checks matching frozen conditions and recomputes the comparison (normal Python with `jsonschema`). Those audits cannot re-read excluded source trees or private journals. The predecessor's initial failed setup is documented in its own report and was not retried under that allocation ID.
