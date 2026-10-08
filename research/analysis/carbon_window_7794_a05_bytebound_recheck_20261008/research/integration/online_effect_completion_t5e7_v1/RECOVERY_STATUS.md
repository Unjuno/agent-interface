# Current publication status — Issue #4321

This recovery preserves the exact frozen source and vendor package. It does
not promote the Issue-reported online-effect result without its formal
evidence capsule.

## Source package checks

The existing read-only publication verifier restored 18 source members,
checked all 32 frozen file hashes and all 15 vendored Git blob identities,
and returned `VERIFIED` with `live_runs: 0`. The restored pure contract suite
passed 16/16 tests and the Python source compiled in a Python 3.13.5 container
(ARM64). These checks validate source integrity and unit contracts only; no
GUI, runtime, or formal session was run.

## Result evidence boundary

Issue #4321 reports `PASS_ONLINE_EFFECT_COMPLETION_SCOPED` for 16 sessions.
The audited branch has no `RESULT_MANIFEST.json`, formal raw/result capsule,
`AUDIT.json`, or `CONTROLS.json`; the publication verifier therefore checked
the source only. The reported result remains historical Issue evidence and
repository status is **HOLD_FORMAL_RESULT_CAPSULE_MISSING** pending exact
result bytes and read-only audit reproduction. No missing rows were
reconstructed and no allocation was rerun.

The bounded claim concerns a cooperative Xvfb/Tk effect sink. It is not
general task success, future persistence, causal authorship, production
authority, or model usefulness. Issue #4321 remains open.
