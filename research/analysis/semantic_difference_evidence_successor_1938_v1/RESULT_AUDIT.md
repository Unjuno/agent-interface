# Result audit

The formal runner is executed exactly once in a clean Ubuntu container by the successor workflow. The audit independently recomputes the bounded contract from the retained raw rows in RESULT.json:

- every row must have exact source-frame, surface, and epoch binding;
- same-frame, surface-replacement, stale-epoch, ambiguous, and malformed controls must be UNKNOWN;
- exact-bound pairs may emit only the declared typed facts;
- authority must remain false for every row;
- model, GUI, network, and task-input counters must be zero;
- reruns, replacements, and tuning must be zero.

Decision is scoped to this finite fixture and does not establish model utility, GUI correctness, latency, token savings, or transfer.
