# Recovery status — Issue #4374

**Disposition: `HOLD_FROZEN_SOURCE_IDENTITIES_ONLY`.** The old remote branch contributes only `FREEZE.json` at commit `1c0900622265c515e30594b2b5a8ff6db4ff2851` (Git blob `370b5e12ca770370ef82ca6517453b62c6fe73af`). That freeze is a preformal commitment (`formal_started: false`) for 28 cases and identifies 11 planned source/plan files; those file bodies are not present in the branch package or this recovery.

Issue #4374 later reports a scoped 28-case `PASS_SOURCE_TIME_EFFECT_ZONE_SCOPED`, but the formal sources, raw case outputs, and audit package are not available here for independent verification. Preserve that as an Issue-reported historical outcome only. No formal allocation was rerun, reconstructed, or relabeled. This freeze-only record does not satisfy the Issue's source/raw delivery or establish application-effect performance; keep the Issue open.

Recovery-only validation: the exact freeze was retained unchanged and parsed as JSON in a network-disabled, read-only Linux/arm64 CPython 3.13.5 container. No study source or formal data was available to execute.
