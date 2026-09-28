# Native Windows junction parity successor for #4882 — allocation 03

This additive package preserves a fresh successor allocation after the two
earlier STOP records. It does not alter #4876, #4882's v1 evidence, or
production broker code.

## H / T / D / C / U

**H.** The pinned #4876 candidate resolver canonicalizes an in-root NTFS
directory junction and rejects an external junction before returning a host
path.

**T.** Allocation `broker-path-windows-junction-4882-20260928-03` was frozen
against main `442ef765598971806dc5d671a223af7b3a711a5f`. The
`resolve_host_path` function AST matches candidate blob
`cdd0e3d57e08a316fc9df6b55abca8c740db070d`. Environment: native Windows 11
10.0.26200, CPython 3.12.10, NTFS. The runner was invoked once. It used a
separate PowerShell script to create two junction fixtures; setup stdout and
stderr were sanitized and retained. No production broker or model CLI ran.

**D.** A scoped PASS would require all nine frozen cases, exact target identity,
live junction identity checks by the independent auditor, and zero audit
errors. Setup failure is STOP and is not a resolver failure.

**C.** Only the host filesystem boundary is tested. No production change,
broker `serve()`, host CLI, model/provider, GUI, user input, GPU, Docker, or
network invocation is part of the allocation.

**U.** A successful candidate-only result would not prove production
remediation, race resistance, real broker file-read behavior, cross-OS parity,
or #3152 model-escalation acceptance.

## Allocation 03 outcome

The runner terminated in setup with `STOP_SETUP_JUNCTION_UNAVAILABLE`; zero of
nine path cases ran. The retained PowerShell stderr identifies a **fixture
script parameter-binding error**: `Get-Item -LiteralPath` received multiple
values without an array. This is not evidence that Windows/NTFS junctions are
unavailable and is not a resolver FAIL/PASS. The raw record is preserved
unchanged at `results/allocation-03/RAW.json`, SHA-256
`b4b1c432f0fa0ed6acb8effc4970c6cef6c99ddfeadf317ac050ea080021f909`.
`STOP_AUDIT.json` reports `PASS_STOP_RECORD_INTEGRITY` with zero errors and
explicitly audits only identities/disposition, not path behavior.

The isolated temp fixture path is omitted from committed output. It contains
only ordinary directories/files; no junction creation completed. Cleanup was
not attempted after the run and is recorded as unverified in `CLEANUP.json`.

### Next allocation gate

Allocation 03 is terminal; do not repair or rerun it. A successor must use a
new allocation ID and frozen output path. Before its formal one-shot run,
validate the exact PowerShell junction constructor without producing junctions
(for example, parser/parameter-binding preflight), ensure the verification
code invokes `Get-Item` once per path, and freeze that source. Retain sanitized
stdout/stderr. If setup succeeds, run the independent live-fixture auditor
before attempting narrow cleanup. If setup fails, retain the typed STOP and do
not retry that allocation.
