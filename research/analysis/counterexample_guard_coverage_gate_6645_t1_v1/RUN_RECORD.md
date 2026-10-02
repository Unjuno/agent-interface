# T1 formal run record

- Allocation: `CGCG-6645-T1-ORB-20261003-01`
- Frozen base main: `b573071d821e20e818304200a9e6ec8c9bbf5670`
- Candidate invocation: 1, exit 0, container `7fe5b04b5c09eaac3dde61cd653591ca255b732f23b314c28377883d5a2fa197`.
- Auditor invocation: 1, exit 0, container `db9499194c8a8bdbb693e3d6854fb3b0d145ad2561719a47d4a63180647ce368`.
- Retries: 0. Candidate and auditor used separate containers with the exact frozen image digest. Both exited 0; both `OOMKilled=false`.
- Candidate raw: `results/formal_01/candidate/raw.json`.
- Independent audit: `results/formal_01/auditor/audit.json`, `PASS_COVERAGE_GATE_SCOPED`, five rows, zero errors.
- Full pre/post Docker inspect output, IDs, exit codes, stdout/raw and stderr are retained in each role's result directory.

## Exact outcome

| Row | Coverage-blind guard | Coverage gate | Fixture oracle class |
|---|---|---|---|
| `valid_complete_coverage` | ADMIT | ADMIT | safe control retained |
| `known_stale_target` | REFUSE | REFUSE | known harmful state refused |
| `hidden_modal_family_harmful` | ADMIT | UNKNOWN | false admission prevented by incomplete-coverage fallback |
| `hidden_modal_family_safe_control` | ADMIT | UNKNOWN | ambiguity conservatively held |
| `unregistered_family` | ADMIT | UNKNOWN | out-of-contract family held |

The finite preregistered gate is met: `PASS_COVERAGE_GATE_SCOPED`. The first
construction attempt had a test-only `NameError`; it was repaired before freeze
and recorded in `CONSTRUCTION.md`. It was not a formal allocation and did not
invoke the candidate or auditor.

Container limits and isolation are configuration evidence. No claim is made
that OrbStack enforced host-level cgroup memory/swap accounting.
