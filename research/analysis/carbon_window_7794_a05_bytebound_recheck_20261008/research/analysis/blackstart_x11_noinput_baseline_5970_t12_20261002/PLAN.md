# Issue #5970 T12 — no-input X event baseline

## H / T / D / C / U

- **H:** The extra observer KeyRelease seen in T9-T11 is not a startup/background event; an armed parent-window observer and X RECORD stream with no XTest/input should remain empty while A and Shift remain up.
- **T:** Launch the exact T3-derived app under private Xvfb, start the T10 parent-only observer and X RECORD core key filter, wait a fixed 500 ms without any input API, then capture observer/RECORD rows and A/Shift keymap before/after. Preserve the executed source hashes and all raw outputs.
- **D:** `PASS_EMPTY_NO_INPUT_BASELINE` if no input was dispatched, both event streams are empty, both keycodes are neutral before/after, and source hashes match. Any key event or nonneutral state is retained as a HOLD/FAIL rather than filtered.
- **C:** One app, one private Xvfb, one observer, one RECORD context, no XTEST extension import or action. Docker Desktop unavailable; WSL2/Xvfb fallback.
- **U:** Whether this establishes why the later extra release appears; event routing under active input; deployed #4135 behavior, recovery/task benefit.

Candidate and independent auditor each run once. No T3-T11 candidate is repeated and no formal #4135 allocation rerun.
