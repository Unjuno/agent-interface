# Issue #3152 — current-main broker path-boundary probe

**Scoped result: `PASS_PATH_CONFINEMENT_GAP_REPRODUCED`.** This is a preformal host-path construction gate only; #3152's formal typed-vs-scalar held-out model-escalation allocation remains unconsumed (0/1).

## H/T/D/C/U

- **H:** the current-main host broker may pass absolute, traversal, or symlink-escaped paths outside its declared repository to the host-side CLI.
- **T:** one Docker Linux/amd64 invocation used exact broker/test blobs from main `fc4159ddd0b546c2adfe58faf8d40771e6e5dfc3` in cached image `ghcr.io/zaproxy/zaproxy:stable@sha256:8d387b1a63e3425beef4846e39719f5af2a787753af2d8b6558c6257d7a577a2` (Python 3.11.2); network none, read-only root, 2 CPU, 2 GiB RAM, 128 PIDs, all capabilities dropped, no-new-privileges; synthetic scratch only on private 16 MiB tmpfs. All 17 current-main broker contract tests passed. One synthetic request used schema `/etc/passwd` and a repo symlink to a sibling temp directory. Only `subprocess.run` was mocked as an argv recorder.
- **D:** `PASS_PATH_CONFINEMENT_GAP_REPRODUCED`: absolute schema, `/repo/../../etc/passwd`, and symlink-escaped working directory crossed the broker-to-host CLI argument boundary; independent raw audit passed and rejected all 8 corruption controls.
- **C:** the mocked child means no real Codex, model/provider, host file read, GUI, input, or task effect occurred.
- **U:** Linux path mapping only; no Windows behavior, data disclosure, production exploitability, evidence-role correctness, reserve safety, or model/task benefit is established.

The original #3152 live transfer remains **HOLD_LIVE_EVIDENCE_INCOMPLETE** and formally 0/1. This result supplies one prerequisite gap to address before that allocation; it does not close or satisfy the issue.

## Post-run source/coordination check

After execution, GitHub `main` advanced twice, ending at `cd2b5e9ae174737c30ca94ac60ef943a77c2b159`. Direct readbacks at both post-run heads confirm both tested source blobs remain unchanged (`5734f54f318db9ac5e96b2bed6f6bed105ac39ff`, `79405a089708a3f2d7c0982192592041125cf0dd`). Issue #3152 is still open; no matching branch or open PR exists. The result remains pinned to its exact source commit and applies to current main's identical broker/test bytes.

## Evidence files

- `PROTOCOL.md`, `PROTOCOL_V2.md`: original and corrected preformal freezes.
- `raw.json`: captured producer JSON from the single scored probe-02 invocation.
- `audit.json`: separate raw-only audit plus corruption controls.
- `construction_stops.json`: two harness/source-verification stops preceding the scored probe, retained without pooling.
- `postrun_main_check.json`: main-head movement and exact unchanged source-blob readback.
