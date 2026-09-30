# Construction 02 — immutable source-capsule hydration

Source freeze: revision 02, commit `fdeca2c76e7f04385de94170f1a07a641f3c1df8`. Formal copied-evidence runner/auditor invocations: 0/1 each.

This container check mounted only the immutable #4447 source capsule. No formal evidence, verifier, or mutation helper was mounted or read. It verifies that the frozen source parts and compressed archive can be reconstructed in a private writable tmpfs before the formal runner is invoked.

Command: `docker run --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=1g --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,noexec,size=128m -v <source-capsule>:/capsule:ro --entrypoint python sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419 -B -S /capsule/restore_source.py /tmp/source`

Observed output:

```text
/capsule/restore_source.py:18: DeprecationWarning: Python 3.14 will, by default, filter extracted tar archives and reject files or modify their metadata. Use the filter argument to control this behavior.
  t.extractall(out)
PASS_SOURCE_RESTORE 19
```

Exit 0. Nineteen source files restored; the capsule script validated all part lengths/hashes and the compressed archive hash before extraction. The warning is from the frozen predecessor restore script and did not affect this Python 3.13 image execution. No retry. This source-only construction does not establish the formal evidence audit outcome.
