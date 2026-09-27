# Versioned read-only audit V2B — CLI construction correction

## Delta from posthoc audit V2 allocation 01

Audit V2 allocation 01 was consumed as `STOP_AUDITOR_UNRECOGNIZED_ARGUMENT`: the auditor's argparse rejected `--evidence /evidence` before entering its audit function. Its stdout, inspect and exit receipts remain in `formal/dockerdesktop-20260926-02/posthoc_audit_v2/`. No raw evidence was read or modified by the audit function and no verdict was produced.

V2B changes only the command line (remove the unsupported `--evidence` option), output path, and container name. It uses the same already-frozen `audit_contract_posthoc_v2.py`, exact formal evidence and hashes, expected decisions, and isolation policy. Its own result directory is distinct. No formal case, broker, or fake executable is invoked.

## H / T / D / C / U

- **H:** A correctly invoked read-only auditor will reproduce all seven raw case classifications and the container isolation evidence, while reporting `AUDIT_PASS_RAW_CASES_HOLD_HOST_DOCKER_EXIT_UNOBSERVED`; it will not infer the missing Docker CLI exit.
- **T:** Run the frozen auditor exactly once in a fresh `python:3.12-slim` Docker Desktop container, network none, read-only source/raw evidence, bounded resources, distinct writable output. The CLI includes only supported options.
- **D:** Return the scoped audit-pass/HOLD status with `errors=[]` only if all pinned bytes, behavior and inspect controls match; otherwise `AUDIT_FAIL`. Container or collector failure is retained as STOP.
- **C:** The original audit 01's sole issue is a missing host CLI exit receipt, not a case-level or isolation discrepancy; V2B tests that claim independently without rewriting audit 01.
- **U:** V2B cannot supply the missing CLI exit receipt, change the formal wrapper STOP, or upgrade the formal allocation to overall PASS.
