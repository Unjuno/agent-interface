# Local shared CI runner qualification

Source tested: 4c1ad74748b3fdec39b0dd2692e4de664dd807db. Network fetch failures
prevented updating to current main or creating the remote PR, so the shared
runner from `.github/workflows/native-mcp-v1.yml` was executed locally in WSL.
This is not a remote CI PASS or a test of an unreceived main revision.

Attempt01 used `/tmp/agent-interface-mcp-venv/bin/python` for both suites.
Protocol passed161 tests. Harness ran68 tests and had28 import errors because
that venv lacks numpy. Its failure and all logs are retained unchanged.

Attempt02 used the runner's existing `--harness-python /usr/bin/python3` option,
matching the interpreter split used by the actual desktop trials. No source,
test or dependency installation changed between attempts. Protocol161 and
harness68 passed:229 tests total. This uses the CI suite definitions, with
separate installed interpreters rather than CI's single pip-built environment.

Command for attempt02 (WSL, repository root):

```text
/tmp/agent-interface-mcp-venv/bin/python -B runtime/integration_checks/native.py --harness-python /usr/bin/python3 --output results-local/native-exact-title-ci-02
```

PYTHONDONTWRITEBYTECODE=1 was set for both. The result files record commands,
runner hash, suite return codes, duration and SHA256 of all four logs per run.
All eight log hashes were checked after copying. These are contract tests,
not extra live GUI trials, independent adoption evidence or performance scores.
The original176-file live archive and its manifest remain unchanged.
