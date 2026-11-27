# Issue #57 stale Calc review before owner admission — r02

This packet demonstrates the known-stale source fast refusal added after r01 exposed an ambiguity in the previous behavior. The test observes and mints a source, waits 20 ms as a controlled stand-in for a pending model response, changes Fake X title metadata, captures a newer sequence, then submits the old reviewed sequence through the public MCP Calc profile.

The server now compares the reviewed sequence to its cached owner snapshot before worker admission. It returns `invalid_request/CALC_REVIEW_SOURCE_STALE` with `operation_invoked=false`, `input_dispatched=false`, no release claim, unknown task effect, and replay denied. The raw owner/MCP receipts contain the two observation generations and the changed title cue. No fake input-state artifact was created. Close returned verified; there was no input to release, so release confirmation remained null.

The child-side profile revalidation remains necessary to cover a source change racing after this parent preflight. Six targeted local tests passed across normal Python and `-O`: stale-source refusal, healthy owned-MCP Calc path, and the provider-ledger/public-MCP/FODS composition. Commands are in `test-results.json`. All retained files are SHA-256 listed in `SHA256SUMS.json`; `source-diff.patch` records this implementation from the stated main base.

## Limits

This simulates the wait interval and title mutation; it does not run a model/provider request or prove provider-to-MCP timing/accounting. It is not a live Calc, WSLc, MAP01, or efficiency result. The earlier pre-fix observation remains separately preserved in r01.
