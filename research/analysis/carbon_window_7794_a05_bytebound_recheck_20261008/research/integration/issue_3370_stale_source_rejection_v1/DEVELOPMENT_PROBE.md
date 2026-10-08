# Development probe — invalid source sequence zero

Before the formal stale-source preregistration, a disposable OrbStack MCP
allocation received one exploratory request with `source_sequence=0`. The MCP
schema rejected it (`ge=1`) before stage publication; no `request-1.json` or
`actions.json` was created. The then-reused comparison client assumed all MCP
error text was JSON and crashed with `JSONDecodeError`; container exit was 1
and normal task cleanup was not verified. Raw start, error response, client and
container logs are retained under `evidence/development_probe_invalid_sequence/raw/`.

This is not formal evidence for stale-source rejection: zero is schema-invalid,
and cleanup was unverified. It motivated the error-safe dedicated client and is
excluded from the formal audit and pass count.
