# Issue #3569 — refreshed same-host route-availability preflight

**Disposition: `STOP_ROUTE_UNAVAILABLE` before model/task calls.** No nonce/image task was issued and no comparative result is claimed.

## H / T / D / C / U

**H.** The same current model host can call Agent Interface through its public MCP route while retaining candidate CLI/API routes and model-visible image delivery. This must be demonstrated before the preregistered model task is attempted.

**T.** One read-only Windows-host availability snapshot on 2026-09-27 06:18:48 JST: `codex --version`, then `codex mcp list`. Codex CLI reported `0.158.0-alpha.2`, exit 0. The sanitized normalized snapshot is [`HOST_STATE.json`](HOST_STATE.json). Listed entries were `codex_app` (disabled / Auth `Unsupported`), `cua_repl` (enabled / Auth `Unsupported`), and `node_repl` (enabled / Auth `Unsupported`). No `agent_interface_integration` or `agent-interface` entry was listed. No MCP server was invoked. Credentials were not inspected, configuration was not changed, and there were zero provider, model, or task calls.

An independent standard-library auditor and four focused tests were then run in the cached local Docker image `python:3.12-slim-bookworm`, immutable image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, Python 3.12.14, with `--pull=never --network none --read-only --memory=512m --cpus=1 --pids-limit=32`, and the source mounted read-only. Both audit and all four tests passed; the audit disposition is `STOP_ROUTE_UNAVAILABLE`, `errors=[]`.

Exact command shape:

```powershell
codex --version
codex mcp list
docker run --rm --pull=never --network none --read-only --memory=512m --cpus=1 --pids-limit=32 -v <snapshot-dir>:/in:ro python:3.12-slim-bookworm python -B -m unittest discover -s /in -p test_audit.py -v
docker run --rm --pull=never --network none --read-only --memory=512m --cpus=1 --pids-limit=32 -v <snapshot-dir>:/in:ro python:3.12-slim-bookworm python -B /in/audit.py
```

**D.** The preregistered task gate requires all routes to be model-visible on the same host before task calls. The current Codex CLI registry has no Agent Interface server; direct API/CLI output through shell would not establish same-model native image delivery. Stop before all task calls, as required. The Docker audit separately rejects a false server-presence summary, an unreported call, duplicate server names, and any claim that a merely configured server alone proves same-model visibility.

**C.** This is a host-specific availability observation, not a transport-quality comparison. The container is used only for independent offline verification because the CLI registry under test is host-specific. No external provider/model, network, GUI, task fixture, credentials, or runtime input was used.

**U.** A missing server in this CLI listing does not prove the public API/CLI are unavailable to other hosts, nor that a different supported host cannot expose the required image/tool routes. It does mean the same-model matched task was not established here. No tokens, cost, correctness, latency, route winner, or efficiency evidence exists.

## Provenance and ownership

- Parent: open Issue #3569, successor to #3544.
- Intake main / branch base: `e4067367d3664578165a7bfd44bc04c01d267eb2`.
- Branch: `research/issue3569-host-availability-20260927`.
- Additive path: `research/integration/issue_3569_host_availability_20260927/`.
- Pre-allocation branch search for `3569` was empty; open PR search returned no matching PR; this path was absent on main.
- No direct model route, host MCP registration, credential, or persistent config was modified.

## File hashes

- `HOST_STATE.json` SHA-256 `7786821c425f369be63d60c81f068cd42e2e517325709f562e9b2373d148a660`
- `audit.py` SHA-256 `144ef1d3ac57c09177ba45b8cc8486d78fc546a301357812fe5cf73b33e25a02`
- `test_audit.py` SHA-256 `4ec59663c45ba1e823ee74197b207c7a591ba120384e16f713a06268b1b9a14a`
