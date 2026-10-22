# A15 handoff correction

This is an append-only correction to the handoff pointer in A15's
[`A15_RESULT.md`](https://github.com/Unjuno/agent-interface/pull/8810/files).
The old pointer names an ignored
`results-local/doom/map01-v39-live-threat-guard-a15-health-policy-guard-20261009/A15_RESULT_PUBLIC.json`
file. The canonical reviewable aggregate is the tracked
[`A15_RESULT_PUBLIC.json`](../map01_v39_live_threat_guard_a15_health_policy_guard_a01_20261009/A15_RESULT_PUBLIC.json).
The retained local and tracked public-summary bytes both have SHA-256
`b764c5f5e2af1c4b2526f4cdd083d58ef7dfa0fc524fdb7eb35a177960ba9b01`.

The ignored A15 output tree contained 3,859 regular files totaling 119,669,935
bytes when inventoried. Its complete relative-path/size/SHA-256 listing is
`A15_RAW_SHA256_MANIFEST.jsonl`, digest
`3c4040312c3b0b625ea80f3b950a933290cf590f92299488e8ec3f2a94c39cc3`. The
local verifier read every listed file and independently matched the public
summary at PR #8810 head `3766e880ca0d52652dc9cc3d7caac766aef716f8`:
`PASS_A15_RAW_CUSTODY`. The output tree itself is not included here.

The readback binds the manifest to local `FREEZE.json`, original `AUDIT.json`,
`A15_RESULT.json`, and `A15_RESULT_PUBLIC.json` hashes. The initial audit remains
FAIL with SHA-256
`fbe97d46f13e657f0eb3832241884ac2b656b1511c41cd024005a01b5279fe74`; A15's
scientific disposition remains HOLD and the candidate was not rerun. This
custody repair neither creates a health-guard exposure nor changes the Issue
#59 live-control gate.
