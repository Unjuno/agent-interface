# Docker IPC schema preflight result (#2818)

After the JSONL parser correction in PR #2826, one host-local broker preflight
successfully extracted exactly one `item.completed` agent message and obtained
a `compiled-form-grounding-v1` payload. The broker returned success and kept
`authority_granted=false`; no GUI operation or task route ran. This is a
schema-bridge preflight only, not a model-quality, GUI-effect, or six-task
result.
