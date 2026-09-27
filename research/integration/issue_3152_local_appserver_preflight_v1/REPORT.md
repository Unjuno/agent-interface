# Issue #3152 — local Windows app-server construction preflight

## H / T / D / C / U

**H.** On this PC, the installed Windows Codex executable may provide the same
stdio JSONL app-server protocol needed by the typed planner client even though
the frozen Node/`codex.js` launcher is unavailable and WSL cannot execute host
Windows binaries.

**T.** Construction-only, not a formal #3152 allocation. Start the installed
`codex.exe app-server --stdio` with app/plugin/browser/computer/code-mode
features disabled and disable only the locally configured `node_repl` MCP.
First check initialization through the repository's unchanged
`CodexAppServerClient`; then make one ephemeral, read-only, schema-constrained
`gpt-5.6-luna`/low turn returning `{"probe":true}`. No image, recovery case,
GUI, action, file write, or other tool was supplied. Formal cases: 0.

Source identity at the local fetch was main `a1a9a7d0abdcdf65d5aba3b74e7f7caf171f2ca4`.
The client and planner-adapter Git blob IDs match that main tree. Host executable:
Codex CLI `0.158.0-alpha.2`, SHA-256
`0122378c15dc0c3c0af0d6addf2dd278125c19676b41fadaa520f89d2c9e0079`.

**D.** The contemporaneous local probe output recorded app-server initialization
and one completed schema-valid model turn. The reported answer was
`{"probe":true}`; reported elapsed time was 5,007,358,700 ns and usage was
8,671 input / 15 output tokens. The process used the local Windows Codex
executable; inference used its configured Codex model endpoint, not a local GPU.
The raw app-server JSONL transcript was not retained, so these are retained
summary claims, not independently replayable protocol evidence.

**C.** A preceding launcher construction attempt that disabled five fixed MCP
names failed before initialization with `invalid transport in mcp_servers.blender`
because Blender was not configured on this host. That failure is retained in
`RESULT.json`; the successful command disabled only the configured
`node_repl`. This points to a launcher-configuration compatibility issue, not
a scientific failure. The successful host executable uses the same app-server
stdio protocol but is not yet proven equivalent to the frozen Node/JS launcher.

**U.** This only establishes a local protocol/model-call path. It does not test
typed-vs-scalar admission, any held-out recovery case, real task outcome, or
effect verification, and it does not satisfy #3152. This was an exploratory
construction probe rather than a prospectively frozen formal allocation; the
formal count remains zero. The app-server had to run on Windows because WSL
interop is disabled; Docker was used only for the independent, networkless
record-summary audit.

## Reproduction boundary

The exact executable, source identities, observed response summary, failed
launcher attempt, resource restrictions for the Docker audit, and limitations
are machine-readable in `RESULT.json`. `audit.py` recomputes the executable and
source hashes and checks summary-field consistency only. Its
`PASS_PREFLIGHT_SUMMARY_SHAPE_ONLY` result is not a protocol-integrity audit
and does not independently prove that the model call occurred; no transcript
is retained or replayed.
