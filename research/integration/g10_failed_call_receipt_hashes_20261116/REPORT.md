# G10 failed-call receipt hash recovery

## Finding

In the public G10 stdio accounting test, the all-attempt snapshot helper was given the attempt root, while persisted MCP request/report files live under `child-output/<call_id>/`. A failpoint after a completed compiled call retained its call ID and response hash but lost request/report hashes. Both the in-progress snapshot and finalizer now use the child-output directory as the receipt root.

## Verification

The injected failpoint occurs immediately after the completed `interface_guarded_calc_compiled` response. In normal and optimized Python, the test process exits nonzero as intended; the terminal ledger remains `failed` at that phase, with exact request, response and report SHA-256 values. Effect, task success, input release and close remain UNKNOWN/unverified.

The corresponding no-failpoint runs pass 1/1 in normal and optimized modes, retain hashes for the same compiled call, independently verify both saved fixture effects, record verified input release and owner close, and report task success true. These are Fake X/process fixture results; provider usage remains unavailable and the lifecycle duration is not an efficiency comparison.

Raw attempt ledgers and combined stdout/stderr logs are preserved under this directory. Published logs redact the workstation checkout path; original failed-run transcript hashes are retained in local run metadata. Final-source module runs, including the new regression, pass 2/2 normally and under `-O`; exact log hashes and commands are in `CONDITIONS.json`.

## Limits

This fixes receipt-hash completeness for the composed test ledger only. It does not ingest provider usage, establish a live Calc run, or provide the matched cold/warm/invalidation/repair comparison required by Issue #57.
