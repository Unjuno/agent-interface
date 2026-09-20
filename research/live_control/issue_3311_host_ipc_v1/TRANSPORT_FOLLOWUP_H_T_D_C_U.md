# #3311 v1 host-IPC transport follow-up

## H — hypothesis

The existing container-side v1 runner and host-side v1 broker can exchange one bounded, non-authoritative model request across OrbStack shared volumes when both sides use one declared `/repo` mapping and the IPC volume is shared. Before the fix, the one-shot broker reported exit 1 after a successful child exit 0 and omitted the frozen responder instructions from the Codex CLI request.

## T — bounded test

On OrbStack context `orbstack`, use local Linux/arm64 image `agent-interface-3311-runtime-v2:20260920` (`sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`) with `--network none`. Mount a temporary fixture root at `/repo`, IPC at `/ipc`, and a temporary output root at `/out`. Start the existing v1 host broker with a fake Codex CLI and `--once`; execute the existing v1 container runner in handle/no-image mode. The fake CLI verifies that host-visible schema, responder instruction, and workspace files exist, then emits a synthetic thread/message/turn stream. Assert container and broker exit 0, exact request paths, `authority_granted=false`, invocation receipt, and returned event stream. Separately run the existing broker/backend/bridge contract suites.

## D — disposition

`PASS_V1_SHARED_VOLUME_TRANSPORT_ONLY`: the OrbStack round trip passed once; eight broker unit/contract tests and eight related bridge/runner/backend tests passed (16 contract/unit tests total). This does not establish real Codex CLI/model compatibility, a fresh schema-preflight PASS, GUI/task correctness, or any efficiency effect. Earlier v2 path-mapping STOP and #3311 dependency/preflight STOP records are unchanged.

## C — controls

Fake CLI only; unique temporary fixture paths; Linux/arm64 pinned image identity; `--network none`; no GUI app or task input; no authority-bearing request. The broker now refuses paths outside `/repo`, traversal and resolved symlink escapes, verifies schema/instruction/image SHA-256, requires non-authoritative mode/image consistency, forwards `model_instructions_file`, and returns the actual child exit code for `--once`. Its setup refusal is returned as a bounded broker STOP record instead of leaving the container waiting for the full timeout.

## U — unresolved / stop conditions

The current frozen schema preflight still uses a Windows-only CLI path. The next gate is to route a fresh no-image schema preflight through this same host-IPC boundary, record host CLI/runtime identity and usage, then validate the integrated desktop workflow in a separately frozen allocation. No conclusion about #3311's hypothesis is available until that new gate and independent task audit complete.
