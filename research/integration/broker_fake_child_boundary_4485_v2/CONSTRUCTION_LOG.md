# Issue #5036 construction and post-run host checks

## Before the formal result was found

- Exact Docker Desktop image identity: `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e linux/amd64`.
- Source bind mounted read-only; a container-side `sha256sum` of all five source files matched `FREEZE.json` exactly.
- Frozen-image harness tests: 3/3 PASS.
- Disposable `/tmp` mount probe under `--tmpfs /tmp:rw,exec,nosuid,size=16m`: created, chmodded, and executed a fake script; output `tmpfs_exec_ok`.
- The first inline probe command had a quoting SyntaxError; it did not execute a fake child. The corrected disposable probe passed.

## Formal result discovery and no-rerun guard

When this lane reached the final fresh-output preflight, `work/issue5036/out` was already populated. The first host wrapper check failed on an empty `docker ps` result before launching Docker. The corrected wrapper then rejected the non-empty output directory, also before `docker run`. Both checks left the existing evidence unchanged. The retained files were then audited read-only; see `STOP_REPORT.md`.

A parallel coordination lane explicitly confirmed that it did not execute #5036 and did not create this output directory. The initiating process for the already-present execution record could not be identified. No additional formal invocation was made by this lane.

## Remaining

Do not start another container for allocation -02. A fresh successor is needed to test a timeout only after the fake-child start is independently recorded, and to retain a host-side exact invocation receipt before execution. Keep the scientific question scoped to the broker boundary.
