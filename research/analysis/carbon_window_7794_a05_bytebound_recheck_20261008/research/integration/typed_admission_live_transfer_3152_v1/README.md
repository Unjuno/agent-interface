# Typed-admission live-transfer retained-case audit (#3152)

This additive audit asks whether the already-retained adaptive semantic repair model case can serve as a #3152 held-out comparison row. It does not change, replay, or reinterpret that historical allocation.

## H/T/D/C/U

- **H:** the retained model-facing recovery case supplies the required roles, measured observation cost, downstream reserve, both typed/scalar decisions, final task disposition, and verified cleanup needed by #3152.
- **T:** parse the immutable case `report.json` and action/release records in Docker; independently test field presence, exact case SHA-256, completed actions, empty verified releases, and final task output. No model or GUI call.
- **D:** emit `RETAINED_CASE_COMPLETE` only if every required field exists; otherwise `HOLD_LIVE_EVIDENCE_INCOMPLETE`. A held case does not consume or count toward #3152's formal allocation.
- **C:** the case was designed for adaptive semantic repair rather than fidelity-role admission; its schema may not expose the comparison fields even though it has useful model/task evidence.
- **U:** post-hoc audit of one historical case only. It does not compare policies, establish model utility, satisfy a held-out set, or validate current runtime behavior.

The audit is run from immutable source against a read-only mount. The first Docker attempt using the WSL ext4 path from the Windows Docker client failed before container startup because that path was not visible to that client. The same command via the Ubuntu WSL Docker CLI uses Docker Desktop's registered WSL bind mount and is the reproducible route.
