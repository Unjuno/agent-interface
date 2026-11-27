# Current-main local regression recheck — R03

Exact current-main commit `1263068ac473d6e64bad2136282fcfbf9eab666d`, clean dedicated worktree before packet creation, Windows local Python 3.11.9. The runtime cancel/supervisor suite passes 63 tests with one skip in normal and optimized Python. The provider-attempt ledger/public-MCP composition suite passes 33 tests in both modes. Raw combined output, exit codes, conditions and Git blob IDs are retained in this packet.

The composed generation-fence case injects a fake provider response, changes the target generation, and verifies that the actual public compiled FastMCP endpoint rejects input before dispatch. This is contract-level integration evidence; it does not establish real-provider exhaustiveness or usage reconciliation. A source search for `CodexAppServerClient`, `PersistentGroundingModel`, `provider_attempt`, `responses.create`, `chat.completions`, and `create_response` under `runtime/**/*.py` returned no matches. That bounded search is not proof that every possible provider adapter is absent.

The one skipped runtime test is reported by unittest and remains skipped; no live Xvfb, desktop, WSLc, or model call was used. This packet does not establish physical release, MAP01, matched efficiency, or reliability.
