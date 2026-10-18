# Timing privacy and control utility

## Issues #6201 and #8899

**#6201 idea and scoped result.** The earlier synthetic T0 asked whether a lower-trust metadata observer could infer a stipulated private state from event counts, gaps, and payload sizes. Its latest result comment reports a held-out attacker accuracy of 1.0 for adaptive/content-redaction-only schedules and 0.5 for a sink-scoped fixed envelope/no-signal control, while preserving the stipulated public effect and internal safety timestamps. This is a bounded synthetic leakage result, not evidence of a deployed leak or formal noninterference.

**#8899 idea.** The successor asks whether timing can simultaneously be useful to an authorized controller and leak information to a lower-trust observer. It proposes a synthetic frontier across exact event times, bounded-width buckets, and fixed/coarse public envelopes while holding event generation and payload content fixed. Precise internal safety clocks remain separate. Its proposal explicitly excludes delaying or padding release, cancellation, focus-loss, hazard, uncertainty, and user-required events; only declared noncritical synthetic events could be coarsened.

**Current status.** #8899 is open and unverified; no new allocation, implementation, or result is reported. The earlier #6201 result does not establish controller utility or the cost of coarsening. No live user traffic, deployed timing leak, or recommendation to alter safety timing is claimed. See [Issue #6201](https://github.com/Unjuno/agent-interface/issues/6201) and [Issue #8899](https://github.com/Unjuno/agent-interface/issues/8899) for the full source and proposed test.
