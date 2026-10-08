# Root-confined host broker path resolver — construction result (#4876)

## H/T/D/C/U

- **H:** A root-confined resolver preserves canonical in-repository paths and rejects absolute, traversal, ambiguous separator, missing and external-symlink targets.
- **T:** One frozen Linux/amd64 Docker formal-03 invocation used the exact main broker source blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`. A candidate resolver was injected at the broker mapping function. Ten path cases ran; the actual broker `serve()` ran one valid synthetic request with `subprocess.run` replaced by an argument recorder. A separate networkless read-only-source/raw Docker container independently audited raw and ran six copied-evidence mutation controls.
- **D:** Runner: `PASS_PATH_RESOLVER_CONSTRUCTION_SCOPED`, 10/10 path cases, valid broker serve called the mocked subprocess once, authority=false. Independent raw-only audit: `PASS_INDEPENDENT_AUDIT`, errors=[]. Corruption controls: 6/6 rejected. Post-run freeze verification: source hashes all match; Python compilation check PASS.
- **C:** This proves the candidate resolver's declared path policy and a valid path through the broker's serve route only. Host CLI/model/provider was never invoked. Invalid paths were passed directly to candidate resolver tests; they were **not** sent through serve to verify broker rejection receipts.
- **U:** No production fix, exploitability/host file read, Windows path semantics, real CLI/model, typed-vs-scalar live result, or #3152 acceptance. Keep #3152 open. Candidate remains research-only.

## Setup STOPs (preserved, excluded from the 10-row result)

Allocation 01 `broker-path-confinement-4876-20260927-01`: `STOP_SETUP_OUTPUT_DIR_PREEXISTS`; mounted `/out` already existed while runner required a fresh path. Docker exited before any path row or mocked subprocess (0/0).

Allocation 02 `broker-path-confinement-4876-20260927-02`: `STOP_SETUP_NO_TMPFS`; read-only root had no writable temp directory. Python stopped before any path row or mocked subprocess (0/0).

Neither allocation was retried. Formal-03 is a separate allocation with unchanged scientific gates. Its raw decision is reported independently; setup STOPs are not pooled into the scientific denominator.

## Provenance

- Base main: `cd7853030248c0d19293bf573cd7c90109b1a57e`
- Branch: `research/broker-path-confinement-4876-20260927`
- Path: `research/integration/broker_path_confinement_4876_v3/`
- Image: `python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0` (Linux/amd64)
- Docker: `--network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16777216 --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1`
- Runner invocations for formal-03: 1; reruns: 0; post-freeze scientific tuning: 0.
- Raw SHA-256: `7dfad7a97a7c701e73c005e52c3833e9027f640e630bdf89100ff3addf756ddd`
- Independent audit SHA-256: `ca677de278d71f5bda0f720579db7023490db6655079d0200a0d8251c9d54bf2`
- Corruption controls SHA-256: `4b1dd860f9797148759468eb804de1a47cea016b045aed93c3933f11e7484ed8`

See `FREEZE.json`, `RUN_RECORD.md`, `setup_stops.json`, raw JSON and both independent audit artifacts.

