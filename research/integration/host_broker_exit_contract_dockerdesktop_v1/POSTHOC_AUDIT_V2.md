# Versioned read-only audit 02 — runner receipt gap

## Why this separate audit exists

Allocation 02's formal container completed all seven cases and its inspect record shows container exit 0. The frozen audit 01 correctly preserved one unresolved host-wrapper problem as `AUDIT_FAIL`: PowerShell converted unittest progress written to native stderr into a terminating error, so the wrapper's Docker CLI exit code was never observed. That audit's seven case classifications all matched the frozen expectations. The missing CLI exit is not reconstructed or inferred here.

## H / Hypothesis

A separate read-only verifier can independently validate the frozen source identities, every raw evidence byte, all seven scenario classifications and the retained Docker inspection policy without importing the test runner or audit 01. If those checks pass while the Docker CLI exit remains unobserved, the only valid result is `AUDIT_PASS_RAW_CASES_HOLD_HOST_DOCKER_EXIT_UNOBSERVED`, not a formal PASS.

## T / Test

Freeze `audit_contract_posthoc_v2.py` and `POSTHOC_AUDIT_V2_FREEZE.json` before invocation. Run the auditor once in a fresh Docker Desktop container on the pinned Python image with network disabled, read-only root/source/raw evidence, bounded resources, and a separate writable output directory. The auditor independently recomputes the raw inventory and scenario verdicts, validates formal container inspection and verifies audit 01's sole finding. It must not modify or reread evidence through the test runner. Preserve its exact command, stdout, inspect record and exit status.

## D / Decision

- `AUDIT_PASS_RAW_CASES_HOLD_HOST_DOCKER_EXIT_UNOBSERVED` iff every frozen source/evidence hash, case result, isolation setting and audit-01 finding matches, with `errors=[]` and an explicit host-exit HOLD.
- `AUDIT_FAIL` for any integrity, identity, behavioral, or policy discrepancy.
- This cannot convert allocation 02 to an overall PASS, supply the missing Docker CLI exit receipt, or authorize another formal-suite invocation.

## C / Constraints

This is a separately versioned, read-only evidence audit, not a replay. It reads allocation 02's original raw bundle and immutable audit-01 result; it does not invoke the broker, fake executable, model/provider, GUI, or any formal test case. Allocation 01 and allocation 02 outputs remain unchanged.

## U / Scope

Even an audit-02 pass establishes only internally consistent raw case and container-inspection evidence. The formal wrapper's own Docker exit receipt remains missing, so the result remains HOLD for independent integration review.
