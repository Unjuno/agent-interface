# Issue #3644 experiment log

## Preparation

- Pinned local image: `sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`, linux/arm64.
- Construction smoke observed launcher PID 10 and Calc XID owner PID 33 in PGID 10. No group signal was sent.
- First audit-unit run: 3 failing tests due missing synthetic fixture evidence; corrected.
- Second audit-unit run: 1 failing test showed missing direct-launcher reaping check; auditor and fixture corrected.
- Latest audit-unit run: 6/6 PASS in pinned image; Python syntax checks PASS.
- Initial private-display smoke failed because its Xauthority record was invalid. A revised, container-private Xvfb `-ac` smoke then reached READY. No host display is mounted; this setting is restricted to the disposable network-disabled container.
- One early formal-runner invocation stopped at entry because FREEZE.json did not yet exist. The application did not start and no SIGTERM was sent. This was a procedure-order STOP before allocation, not an outcome for the hypothesis.

Formal evidence must be separately run only after source freeze and must not overwrite any preparation records.
