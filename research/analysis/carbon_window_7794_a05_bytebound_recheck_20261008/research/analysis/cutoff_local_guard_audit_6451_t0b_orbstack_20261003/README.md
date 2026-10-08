# Issue #6451 T0b — cutoff-local guard audit with durable raw capture

This is a fresh successor to the consumed T0 allocation that stopped because stdout was truncated and the auditor never ran. The old STOP and sources remain unchanged. T0b narrows the comparator to the preregistered bandwidth and writes complete candidate JSON directly to a dedicated output bind mount before the independent auditor starts.

See [PREREGISTRATION.md](PREREGISTRATION.md), [FREEZE.json](FREEZE.json), [RUNBOOK.md](RUNBOOK.md), and the post-run [REPORT.md](REPORT.md). This is synthetic method evidence only; it does not establish a live GUI guard, causal effect, safety, or global policy benefit.
