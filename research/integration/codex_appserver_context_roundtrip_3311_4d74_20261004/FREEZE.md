# Frozen local app-server context round trip

- Base main commit: `b84fc9a4fc14608c729e7eda2ee32ba6b4ac0ab4`.
- App-server executable: ChatGPT.app-bundled
  `Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`.
- Reported version: `codex-cli 0.159.0-alpha.12.1`.
- Binary SHA256: `1180e2d56ea06ec583092acd933345685da3441cb1769a436d76dbf320613e75`.
- Executed runner SHA256 (local private copy): `49468acd7b89fb5d0769617f8487d6fbb09e9c409c8846a7a6140f09b386528a`.
- Public safe runner SHA256: `0b34e2ba978776be139f17bb1b08e638a343567d79e750a7c3f4481f206ad6ca`.
- Auditor SHA256: `8054e8dd8f07e451eefa3f153b76561084e3af9f6156a3d0d6d671e617ff42d1`.
- Public-derivative auditor SHA256: `3ad204437483c8cb8c144c8cecf4b5d36d738e736dbb3960ebcd947b854bed63`.
- Redaction adapter SHA256: `f896f57c69e2fe74aa674e200acbb101c07f3bce9dea1af2d6b8dee5ae817f2f`.
- Experiment command: `python3 research/integration/codex_appserver_context_roundtrip_3311_4d74_20261004/run_roundtrip.py`.
- Tool result: one `inputText` item containing
  `PARTIAL_STATE=SAFE_YIELD; reason=effect_unavailable; completed_transitions=1; second_requested_input=NOT_RUN; saved_cells=13,41,533; next_row=BLANK`, followed by one `inputImage` item containing the exact G18 final PNG as a PNG data URI; outer `success=true`.
- Image source: PR #7221 retained G18 final capture
  `research/integration/calc_live_reobserve_3311_4d74_20261004/calc-live-reobserve-4d74/runs/live_reobserve18/guarded/images/64ed5a28faa24491b5725e05d086b5c6.png`.
- Expected image SHA256: `6331fd4bb0f62dbb6d8492e0c71a4ad6bf1b98091f39b452e2279e7cfd3e6bcf`.
- Model request count: exactly two, both delivered to an in-process HTTP server bound to `127.0.0.1`; first requests one fixed function call, second returns one fixed message.
- Private first raw SHA256: `00dc26ec7d69abeb5f805166c738c8a0ce769fd92e9229407c6e4d10ed7c0800`; it contained ambient user-local Codex instructions/memory, went only to loopback, and is excluded from Git. Public text is an allowlisted derivative, with hashes/byte counts for redacted fragments.
- The frozen runner captured full provider-request text in its local raw. Its byte-identical source is retained as ignored `run_roundtrip.private.py`; public `run_roundtrip.py` is a post-run safe reproduction adapter that hashes/omits non-allowlisted text at collection time. The source distinction and derivative are recorded in `REDACTION_PROVENANCE.json`; no experiment rerun occurred during redaction.
- Thread: one ephemeral thread, read-only sandbox, one registered tool, model string `gpt-6.1-sol`, low reasoning effort. No shell/browser/computer-use tools or external provider is configured.
- Allocation: local app-server protocol diagnostic only. No WSLc, Docker container, GUI, native input, external inference/provider request, real provider credential, or G18/G17 allocation replay. The provider base URL was loopback-only; OS-level egress was not packet-audited.
- Stop: any third Responses request, unexpected RPC, failed dynamic-tool result, unrecognized version, missing partial marker/image bytes, or nonzero app-server exit is retained as `STOP` or auditor failure; no rerun may overwrite the first `RAW.json`.

The source image is a public G18 artifact copied byte-for-byte into this package. A local mock endpoint reveals what the bundled app-server sends onward; it cannot establish remote-provider receipt or model attention. This is not the WSLc server build used in G18 and makes no live/compiled efficacy, reliability, efficiency, or task-completion claim.
