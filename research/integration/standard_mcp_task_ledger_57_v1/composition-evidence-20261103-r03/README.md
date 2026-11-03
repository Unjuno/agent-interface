# Issue #57 Calc composed ambiguous OCR evidence — r03

This retained run adds an ambiguous OCR outcome to the registered Calc profile path over the synthetic Fake App Server → public Relay/MCP → owned Fake X route.

## Frozen condition

After one verified entry transition, Fake X returns two high-confidence OCR rows for the same expected cell. The cell parser must classify the duplicate as unknown. The profile must yield before a second input or Save, retain a verified release, keep task success unknown, and deny replay.

## Observed result

`boundary-results.json` records five provider attempts (one timed-out preflight with unavailable usage and four completed synthetic generations). The ambiguous attempt returned `SAFE_YIELD/effect_unavailable` after one transition; release was verified, `task_success` remained null, and replay was denied. The positive task was independently parsed as A1=731/A2=864. Wrong-value and unknown OCR controls also yielded after one released transition.

Four targeted tests passed: the direct owned-MCP boundary and full provider-ledger/public-MCP composition, each under normal Python and `-O`. Exact commands and outcomes are in `test-results.json`. The raw provider ledger, provider call, protocol, runtime receipts, and source diff are retained here.

## Limits

This is a synthetic regression result. No physical Calc, actual model/provider, provider billing reconciliation, Docker execution, WSLc, MAP01, or efficiency comparison was performed. It proves only this composed Fake X condition and does not close Issue #57.
