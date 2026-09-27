# Interpretation: notification eligibility is not a delivery deadline

This explanatory note does not modify the frozen experiment, schedule or decision gates. The main distinction follows directly from the policy definitions; measured execution tests the declared implementation boundary.

Let `t1 <= t2 <= ...` be actual observations of the same unresolved gap identity. Let `N=3` and let `B=80 ms`. Time is measured in one monotonic domain.

## Observation count

The first count-triggered notification is at `tN`. Its elapsed age is

```
tN - t1 = (t2 - t1) + ... + (tN - t(N-1)).
```

Without restrictions on observation spacing, a fixed N implies neither a positive minimum elapsed wait nor a finite upper bound. Fast observers can produce three observations quickly; an inactive observer can wait indefinitely. This is a property of the definition, not a newly discovered defect in #926.

## Elapsed eligibility sampled by polling

The elapsed-arm first notification time is

```
tau = min { tk : tk - t1 >= B }.
```

If no such future observation occurs, there is no notification. When it occurs, its age is at least B. If a *future* inter-observation gap is guaranteed to be at most Delta while the gap stays unresolved, then

```
B <= tau - t1 < B + Delta.
```

A measured past maximum poll gap is not a guarantee on future Delta. If host transport delay is also bounded above by R, the host receipt age is below `B + Delta + R` under these assumptions. The present study measures host receipt timestamps but establishes neither a future Delta nor a future R. It does not measure model consumption.

Thus a caller requiring notification *by* a deadline needs an explicit live scheduling/transport contract, not just a timestamp comparison executed when it eventually polls. No new scheduler or watcher is introduced here.

## State and authority

Time state belongs to one exact gap identity. Appending a tail event does not resolve the missing head predecessor. Actual contiguous progress ends the old gap; a later missing sequence starts a new count/timer. Stable notification replay must not advance ACK, erase pending data, or give permission to replay an uncertain action.

The candidate's timer is process-local. It is not durably restored on restart. The inherited SQLite model stores event identity and payload digests, not recoverable application payload content. Neither timer persistence nor a usable durable inbox follows from this study.

## What the comparison can decide

It can show that count-based and elapsed-based eligibility implement different policies, that a scoped elapsed guard survives the declared real process/SQLite cases, and that the evidence independently reconstructs. It cannot choose which policy is economically best, prescribe 80 ms, refute the historical count-policy PASS, or establish a finished live producer/model feedback path.
