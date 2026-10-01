# Issue #2849 OrbStack real-model preflight

This additive research artifact records one real host-model IPC schema
preflight attempt through the latest #3647 selected backend. The predeclared
runner gate **failed** even though the host CLI returned a valid schema-shaped
assistant response. The evidence is intentionally not promoted to an accepted
preflight or six-task result.

- Read [RESULT.md](RESULT.md) for H/T/D/C/U, the failure classification, and
  interpretation limits.
- `PRE-REGISTRATION.md` and `PRE-REGISTRATION-ADDENDUM.md` preserve the gate
  and the pre-model harness setup correction.
- `evidence/attempts-live-v2/plain/` contains the one real IPC request,
  unmodified host event stream and broker receipt, container/client outputs,
  and independent offline audit.
- `evidence/attempts-live-v1/` contains the failed harness initialization; it
  made no model request and is not counted as an experimental attempt.
- `run_preflight_experiment.py` and `audit_failed_preflight.py` are the
  experiment and offline-audit scripts. The exact inputs are pinned by commit
  and SHA-256 in the pre-registration.
- `Dockerfile.audit` and `requirements-audit.lock` describe the offline audit
  environment. The original auditor image ID is recorded in its retained
  command receipt.
- Run `python3 validate_bundle.py --write-manifest` to verify the frozen
  result structure and generate `SHA256SUMS`; run without the flag to verify
  an existing manifest.

This report does not modify PR #3647, alter prior #2849 records, or close the
six-task allocation question. The next code change needs a fresh successor
experiment and its own preregistration; it is deliberately not smuggled into
this failure report.
