# First standard-caller blocked-release Xvfb outcome

This packet preserves the first run of the standard-MCP blocked-release
integration test. It is a failed test-configuration attempt, not an input
release experiment result.

## Frozen source and runner

- PR: [#9171](https://github.com/Unjuno/agent-interface/pull/9171)
- PR head: `6c69f595c0e1d61b0bad0568fde3d05c5d3e841b`
- Workflow run: [39226642774](https://github.com/Unjuno/agent-interface/actions/runs/39226642774)
- Workflow merge-ref SHA recorded by the report: `73b1347d265234433a9458dc8b19d9d189fba089`
- Job: `x11-integration`, completed with failure at the private Xvfb test step
- Environment: Ubuntu x86_64, Python 3.12.15, Xvfb package `2:21.1.12-1ubuntu1.8`
- Xvfb binary SHA-256: `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`
- Original artifact ZIP SHA-256: `faf584731339278bde84395701a0ba24cd3d04cfdd9c7993d075a481f9029e51`
- Retained [raw report](first-outcome.json), SHA-256: `9cab3d331b5fc6a3afaedf558d129bc083bc45f56acec8697d0e2c768aada5b`

## Outcome and limit

The caller observed the synthetic Xvfb window and returned a 64-hex
`process_generation`, but the `pointer_binding` had no `window_generation`.
The test asserted that value before dispatching any input and failed with
`AssertionError: Regex didn't match: '^[0-9a-f]{64}$' not found in ''`.
Inspection of the exact source showed that the `create_server` call enabled
process identity, query worker, and owned process, but omitted
`guarded_window_lifecycle=True`; the adjacent passing generation integration
test enables that option.

The report confirms `input_before_cancel`, `cancel`, terminal result, task
effect, and independent release readback are all absent. No input was dispatched
and no owner release was attempted. The workflow artifact contains the JSON
only; the observation-image copy occurs after the failing assertion and was not
retained. The raw file above is an exact copy of the downloaded report; its
hash is recorded so the first outcome remains auditable.

The corrected test configuration is an additive source revision. Any later
pass or failure must be recorded separately and cannot rewrite this result.
