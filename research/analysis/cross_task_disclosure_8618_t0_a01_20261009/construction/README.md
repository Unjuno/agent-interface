# Construction record

Allocation `8618-T0-A01-20261009` has not been formally invoked. This directory contains pre-freeze construction checks and their distinct outputs.

- Native candidate construction: 14 policy rows in `candidate.jsonl`.
- Initial construction auditor output: `audit_v1.json` records one auditor defect. Auditor v1 compared the public-control action id to an oracle boolean. That failure is retained unchanged.
- Corrected independent audit: `audit_v2.json` (v2 logic) and `audit_sandbox_v2.json` each report `PASS_METHOD_SCOPED`, 14 rows, zero unauthorized gated secret effects, seven unauthorized instruction-only baseline effects, two exact-grant releases (red and blue), seven equivalent general completions, passing public and capability controls.
- Binding/payload corruption checks: `mutation_controls.json` and `mutation_controls_v2.json` preserve the four source, recipient, dependency, and payload mutation results; all four fail closed to the certified general action.
- Network denial: `no_network_validation.json` records the macOS sandbox profile denying loopback socket connect with `EPERM(1)`. The sandboxed construction candidate and separate sandboxed audit both passed.
- Container probe: `orbstack_probe.txt` records that OrbStack reported Running but its read-only Docker inventory failed on a missing/unsupported content blob. No container was launched or modified.
- `attempt-01_command-error.txt` records an initial auditor command typo before it read any raw data. The candidate output was not rerun for that path correction.

These are construction results, separate from the single formal allocation frozen in `FREEZE.json`.
