# A01 — retained A04 coast-monitor component replay

## Result

`PASS_SCOPED_TRACE_APPLICATION`. The fixed five-point, two-of-three candidate and an independently written raw-row oracle both first triggered in each of the five preregistered unauthored coast windows: decisions 0, 1, 2, 3, and 5. Decision 4 remains excluded. The five trigger sequences are 5, 98, 130, 178, and 221. All occurred before the corresponding recorded planner terminal.

| Decision | Baseline health | Window samples | First trigger sequence / health | Trigger after window start | Before planner terminal |
| --- | ---: | ---: | --- | ---: | ---: |
| 0 | 97 | 69 | 5 / 91 | 778.308 ms | 18,868.564 ms |
| 1 | 79 | 45 | 98 / 74 | 7,356.755 ms | 5,637.717 ms |
| 2 | 68 | 36 | 130 / 63 | 3,530.931 ms | 6,627.866 ms |
| 3 | 46 | 39 | 178 / 38 | 6,407.947 ms | 4,532.443 ms |
| 5 | 30 | 45 | 221 / 24 | 1,024.761 ms | 11,676.209 ms |

The runtime predicate can identify these saved trace crossings before the recorded planner terminal. This is only a component replay over existing emitted typed observations; it does not establish that a real consumer would have received the signal, canceled work, or changed subsequent behavior.

## Method

The candidate rule and source were frozen from PR #7527 head `1c12f87d9316f2faa3b2e4b5da55f23ceb2296d4`: minimum health drop 5, 2 low observations in the latest 3. Input is A04 PR #7990 head `3c6862937f30a22aad6380699f23da92d5d2c6f9`, retained ZIP SHA-256 `b6e8529a51e89e6f1c51374fbd27f121bab594c92014ee2fe73aa2f94ef98163`.

For each selected decision, the closed replay window starts at `planner_terminal_observed_ns - model_ns` and ends at the recorded planner terminal. Only typed-health rows in the corresponding `cover-i` or `cover-i-renew-1` stream whose `emit_ns` falls inside that window are evaluated. Baseline is the latest valid typed-health row emitted at or before the window start. Each trace is censored at the first trigger. Decision 4 is excluded as authored. No threshold/window search was performed.

The candidate implementation and independent oracle are separate code paths in `CANDIDATE.py` and `ORACLE.py`; the expected first-trigger rows are frozen in `RESULTS.json`. Scope decision was PASS only on exact row agreement, all five pre-terminal triggers, and preserved exclusion of decision 4.

## Limitations

This is retrospective application of an exploratory rule, not an efficacy estimate or counterfactual recovery estimate. The event stream records `emit_ns`; exact scheduling and consumer delivery are unavailable. A04 source provenance remains unresolved: its source archive freeze points to main `6860b585305e539ec93896f5adcbf658cbbd8592`, and independent review found a staged controller source hash mismatch against that frozen main. Current main at replay freeze is `d9bb339b0ba9285cdef57fc347437d25e5943ef1`; its V39 source being unchanged does not repair the original provenance gap. Retained original A04 outcomes remain authoritative.

No game, model, GUI, input, container, or GPU was used. The consumed A04 allocation was not rerun.

