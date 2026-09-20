# Issue #3756 — formal-02 successor allocation

## H / T / D / C / U

- **H:** The exact current-main X11 backend blob `9cae101a219348077668c8fc086acf8e13154afe` resolves formula symbols from the active German XKB map and delivers exactly `=B2*A2` through XTEST to a fresh xev receiver. A late unsupported `€` is rejected during preflight with zero emissions and zero receiver KeyPress events.
- **T:** Single allocation `issue3733-german-xkb-text-orbstack-formal-02`, based on main `76965311d899815174b5ed081ff439bd4533ef63`. Four distinct Xvfb servers in order: three US-baseline→German rows and one US control. Apply `setxkbmap -layout de` once per German row. Close the original Xlib display after the transition; a fresh client must observe and serialize the active core mapping/levels before candidate construction. Parse xev's two window IDs whether same-line or separate-line. Candidate runs only after layout/server/fresh-client gates. Preserve both event logs, maps, cleanup status, hashes, and all row data.
- **D:** Scoped PASS requires 4/4 successful rows, exact lookup text and key press/release trace for the formula, active-map-consistent plan, no emitted event for unsupported preflight, and independent audit with no findings/integrity errors. Candidate semantic discrepancy is FAIL. Any setup, environment, integrity, timeout, or incomplete issue is STOP/HOLD, never semantic FAIL/PASS.
- **C:** OrbStack Docker Engine 29.4.0, linux/arm64; immutable image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`; network disabled; read-only root, source, harness and predecessor result; only `results/formal-02` writable. No host display/input or external app/data. No pull, package install, candidate source modification, or replay of formal-01. Formal-01 raw SHA-256 is recorded by the new raw as predecessor linkage. The read-only harness mount also exposes, but does not alter, predecessor evidence.
- **U:** Standard two-level German XKB/private Xvfb and this backend only. No Calc/task effect, hardware keyboard, level-3/Compose/dead keys/IME, other layout/backend, production or user-facing claim.

## Source and frozen harness

Candidate: `runtime/backends/x11_v1/backend.py`, blob `9cae101a219348077668c8fc086acf8e13154afe`, SHA-256 `3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8`. Runtime closure is pinned in `source_manifest_v2.json`; base runtime tree blobs are X11 `0a497398c7fd0dabbf75565f4be02eb24f6b0664` and core `1209a89e04eb820d6be7dd3f3390adb07d0d3afc`.

Pinned runner `run_v2.py` fixes the one-line xev parser and explicitly opens a fresh Xlib display after layout application. `audit_v2.py` independently parses event logs, checks raw artifact inventory/source identity/predecessor linkage, validates map and cleanup gates, and classifies stop/fail/pass. Both are frozen by the commit containing this preregistration. Before invocation, run static AST/parser checks only; no candidate input is sent by that check.

## One-shot command

Run once after pushing the frozen commit. Verify `results/formal-02/` is empty and the immutable image resolves to the pinned image ID. The full harness is read-only; formal-01 is under the read-only harness mount. Container stdout/stderr are separately retained under `results/host/`.

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD/runtime:/src/runtime:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v1:/harness:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v1/results/formal-02:/out:rw" \
  -e PYTHONPATH=/src --entrypoint python3 \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/run_v2.py /out
```

Independent audit is one separate, fresh, no-network container invocation with runtime and formal-02 mounted read-only and only `results/independent-02/` writable; invoke `/harness/audit_v2.py /formal /audit`. Preserve both command logs and exit codes. The auditor does not import or execute candidate code.

## Frozen hashes

- Base main: `76965311d899815174b5ed081ff439bd4533ef63`.
- Candidate blob: `9cae101a219348077668c8fc086acf8e13154afe`.
- Runner SHA-256: `318be58b60d83db7c9888674e82afec6d5e346cf731200999d79f394e120be90`.
- Auditor SHA-256: `4c0f4f949c6098a10118644f1e769965e68d09224811430ff001d73ef7e1bbd9`.
- Manifest SHA-256: `a5472f0981214f9effbd97c34b1e9d97e87c299b59f7ab34072ab304e3deb3a8`.
