# Reviewed-target single-replan Fake X composition evidence

Status: `PASS_LOCAL_COMPOSITION_ONLY`; no formal allocation, model, WSLc, Docker, or physical GUI input.

- Date: 2026-10-24 Asia/Tokyo
- Base commit: `937f2229abd6cb4752f62dc1b1f6a1500f18205c`
- Branch: `fix/v39-finite-observer-recovery-20261024`
- Test source: `../test_mcp_endpoint_composition.py`
- Harness: public FastMCP endpoint and Relay with local Fake X owner; provider is an injected deterministic callable.

## Protocol and conditions

1. Observe synthetic process generation `a…a` and mint alias `field`.
2. Change the fixture generation marker to `b…b` after the first provider response and before compiled tool dispatch.
3. Require the first compiled call to return `SAFE_YIELD` / `association_changed`, zero completed transitions, one `admission_refused`, and no action terminal.
4. Explicitly review the same window. Require a newer observation sequence, generation `b…b`, the same live owner and no tracked key/button obligations or pending recovery.
5. Mint `field_recovered` from that reviewed source. Require the mint receipt to bind to the same reviewed sequence, owner, scope and surface.
6. Before any second tool dispatch, require the generated profile to use the new alias and exact minted offset for the reviewed scope/surface and to contain no old target aliases.
7. Permit at most one new provider attempt and one compiled tool call; no loop or replay.
8. Independently score the synthetic app's final RGB state and retain the terminal action release receipt.

Negative controls verify that a refused review starts no second attempt and that old-alias arguments fail before tool dispatch.

## Outcome

The positive path passed: initial generation was refused before input; the reviewed `b…b` plan completed one transition; the action receipt reported `release_verified=true`; an independent synthetic pixel oracle observed the expected state change. `task_success` on the runtime tool response remained null. Ledger totals: two provider attempts, six MCP calls, 22 input tokens and 8 output tokens.

Normal and optimized runs of the integration, guarded-recovery and interruption-receipt suites each passed 22 tests. Exact stdout is retained in this packet. Test assertions use `unittest`; the optimized pytest warning about bare Python `assert` does not disable them.

Raw provider request/response bytes, public-MCP request/response envelopes, attempt ledger, Fake X reports/images, initial/final synthetic application states and score bytes are under `run/`. `SHA256SUMS` covers this packet. `source-SHA256SUMS` pins the source/test/document files in this branch.

## Limits

This result exercises a local Fake X adapter. It does not prove physical/native input release, a hard release deadline under permanently blocked platform I/O, provider-log exhaustiveness, live GUI task success, WSLc availability, MAP01, or matched efficiency/reliability. The independent score validates this synthetic pixel fixture only.
