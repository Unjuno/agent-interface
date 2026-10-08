# #2558 host-local model-boundary replay

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: the host-local Codex runner can consume a Docker-produced observation image and return the existing compiled grounding contract without granting action authority.
- T: replay the retained native Docker observation through host-local `codex exec`; validate the returned structured answer inside a fresh OrbStack Docker container using the frozen compiled-grounding schema.
- D: source observation `runtime/results/native-docker-integration-2558-v2/bridge/images/12cfa97a5c9841be9a2efef6ad4a1d16.png`; image SHA256 `859b236d7685eff2fbe8c2ef9bb719dedc1db827feaa6f52b201cfb626602b89`; model `gpt-5.6-luna`, low effort; host command exit 0; usage 13,427 input / 396 output / 281 reasoning; returned field (130,55), submit (0,0), and required revalidation method. OrbStack validation container returned `schema_valid=true`. Events SHA256 `2aac721e36afe0b1fa8338db510999c2a81a14d61c5a8a362bd1895c0e9a26f7`.
- C: `PASS_MODEL_BOUNDARY_REPLAY_ONLY`. The returned answer is schema-valid and authority remains false, but this is not a fresh GUI allocation and no GUI input or task-success claim is made.
- U: wire this boundary into a fresh OrbStack GUI allocation, then pass the plan through independent focus/geometry/pixel/effect gates before any action.

## Provenance

- Docker validation context: `orbstack`
- Docker Server: 29.4.0
- Architecture: linux/aarch64
- OrbStack: 2.2.3
- Frozen schema SHA256: `a1a5901b84656375657538d2dccb975e3b40a5b22272abbab487c54904db1d0f`

This result supplements, and does not replace, #2620, #2623, or the immutable #57 result.