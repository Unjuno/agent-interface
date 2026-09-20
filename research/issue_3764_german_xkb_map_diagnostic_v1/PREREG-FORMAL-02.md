# Issue #3768 — formal-02 map-representation diagnostic

## H / T / D / C / U

- **H:** The German XKB server dump and fresh Python-Xlib core mapping may disagree after one `setxkbmap -layout de`; the disagreement may reflect distinct XKB/core-map semantics or a capture defect.
- **T:** One allocation `issue3733-german-xkb-map-diagnostic-formal-02`; fresh German-transition and US-control Xvfb servers. Capture baseline/after query, xkbcomp dump, full Xlib keyboard map and selected symbols. No `xmodmap` (confirmed absent), package installation, Agent Interface import, XTEST input, or host UI. Save exact stdout/stderr and hashes. Audit in a second fresh container.
- **D:** `PASS_DIAGNOSTIC_SCOPED` if the formal captures the German transition in query+xkbcomp, both Xlib snapshots and US control, cleanup, and exact artifact inventory; whether the Xlib map changed is the diagnostic result, not a pass/fail gate. STOP for setup failure or missing/inconsistent evidence; integrity error is audit FAIL. This establishes no candidate text-delivery result.
- **C:** OrbStack, Linux/arm64; pinned image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`; network none; read-only root/harness; only dedicated formal output mount writable; host logs outside harness/output mount. Runtime/source files are not modified.
- **U:** Private Xvfb/XKB representations only. No candidate, XTEST input, application effect, hardware layout, or product claim.

## Frozen source/environment

Repository base: `e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8`. This diagnostic runner imports only Python-Xlib; it does not import runtime candidate code. Formal-01 of this diagnostic stopped because xmodmap is absent and remains unchanged. `run_v2.py` and `audit_v2.py` are frozen by this preregistration commit.

## One-shot commands

Verify both output directories are empty. Run formal with `/harness` read-only and only `/out` writable; preserve host stdout/stderr under `results/host/formal-02.container.log`. Never retry if `/out` contains any file.

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 96 \
  --tmpfs /tmp:rw,nosuid,nodev,size=32m \
  -v "$PWD/research/issue_3764_german_xkb_map_diagnostic_v1:/harness:ro" \
  -v "$PWD/research/issue_3764_german_xkb_map_diagnostic_v1/results/formal-02:/out:rw" \
  --entrypoint python3 agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/run_v2.py /out
```

Audit in a separate fresh no-network container with formal output mounted read-only and only `results/independent-02/` writable, invoking `/harness/audit_v2.py /formal /audit`.

## Frozen hashes

- `run_v2.py` SHA-256: `9b664caf6b5644539869168a2ba47349526e9e8d73fadf82068f16a308982b49`
- `audit_v2.py` SHA-256: `bb332ce2d14413240702f9596ecc4a01b994c70403107b25cbc01b7145e6b34d`
