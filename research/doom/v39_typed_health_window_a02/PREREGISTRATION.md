# V39 typed-health short-window coalescing A02 — parser-safe successor preregistration

Status: FROZEN AFTER A01 PRE-CANDIDATE RUNNER STOP; BEFORE A02 CANDIDATE RUN
Predecessor: `research/doom/v39_typed_health_window_a01/PREREGISTRATION.md`
Preserved predecessor outcome: `research/doom/v39_typed_health_window_a01/runner-stop.json`
Base source commit remains `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`.

## Why A02 exists

A01 stopped before candidate evaluation because the invoking Node command did not split the JSONL correctly. A02 preserves that STOP and defines a distinct, parser-hardened successor execution. It does not alter A01's preregistration or claim A01 produced data. The immutable source blobs and scientific rule remain unchanged; only the runner protocol is versioned to validate record framing before parsing.

## H/T/D/C/U

- **H:** In the retained six-wait v39 typed-health stream, two downward health transitions within a short interval may be observed before a model wait completes on worsening no-policy waits, while a stable no-policy wait remains untriggered.
- **T:** Replay the exact ordered `typed_observation` records per report model-wait interval. A downward transition is an adjacent pair of valid observed health values where the current value is strictly lower. Trigger at the second such transition when two decreases are within W. Sweep W in {0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0} seconds and report all six waits; do not select a winner after seeing results.
- **D:** Same pinned report blob `bff2459036dcdcc44ed100b0c0bc657e1bb8e69a`, event-stream blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`, and guard blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`; base main `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`. Expected event framing: 634 non-empty JSONL records; expected typed observation rows: 218.
- **C:** Fetch each input by pinned commit path; split JSONL by literal LF after removing CR; assert exact record counts and parse every record before analysis. Valid health rows require status `observed` and numeric value; unknown/missing rows clear the previous-value chain. Only transitions whose second sample lies inside the wait count. Trigger time is the second decrease's capture time. No runtime, model, game, input, acknowledgement, or task outcome is simulated.
- **U:** One retrospective trace only. The stable control consists of a single wait and cannot calibrate a false-interrupt rate. Output cannot establish event meaning, causal benefit, or live authority.

## Decision gates

- **PASS_SCOPED:** source identifiers/counts validate, all six windows parse, results are deterministic under a second independent calculation, and source artifacts remain unchanged.
- **FAIL:** frozen scientific rule evaluates but hypothesis is contradicted; preserve raw outcome.
- **HOLD:** any pinned source artifact is missing or inconsistent.
- **STOP:** framing/count/source validation fails, or execution would cross into runtime/game/model/input.
- Do not retry A02 after a failed/STOP candidate execution. Do not treat any replay output as permission to interrupt a live planner.
