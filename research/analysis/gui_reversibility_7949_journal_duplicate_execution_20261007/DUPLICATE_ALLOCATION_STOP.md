# STOP — duplicate of consumed allocation

On 2026-10-07, after the local writer/observer chain, candidate, and auditor had completed, the full GitHub Issue #8300 timeline was inspected. It already contained a pre-run freeze and a formal result for allocation `GUI-REVERSIBILITY-7949-JOURNAL-A01-20261007` (Issue comments #6037745388 and #6037757687). The local run mistakenly reused the same allocation ID and overlapping six-case question.

Disposition: **`STOP_DUPLICATE_ALLOCATION_ALREADY_CONSUMED`**. The local raw files and embedded PASS payloads are preserved solely as a custody record of this protocol deviation. They are not a new independent result, are not pooled with, or substituted for, the earlier A01 outputs, and do not replace or qualify the earlier result. No retries occurred after discovery. No container state was modified.

The error was failure to inspect the full Issue discussion and prior allocations before creating the new freeze. Future work must first reconcile all Issue comments, existing artifact paths, branches, and PRs, and then use a genuinely distinct allocation ID/path. Any possible next experiment must test a distinct unresolved question rather than repeat consumed A01.
