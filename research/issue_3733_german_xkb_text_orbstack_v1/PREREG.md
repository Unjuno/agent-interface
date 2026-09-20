# Issue #3733 — formal OrbStack allocation preregistration

## H / T / D / C / U

- **H — hypothesis:** On the standard German XKB layout, exact current-main `X11Backend._text_plan` resolves `=` and `*` from the active server map, and a fresh private receiver decodes the actual XTEST events as exactly `=B2*A2`. A late unsupported trailing `€` is refused before any event.
- **T — target:** One formal allocation, `issue3733-german-xkb-text-orbstack-formal-01`, against main commit `eca4bcc1ee839b80442397e27f238c97d6dd6bb4`. Freeze source files in `source_manifest.json`, runner and auditor by this commit. In one no-network container, start four sequential, distinct Xvfb servers (three standard-German rows, one default-US control); on each, verify XKEYBOARD/XTEST and US baseline. For each German server invoke exactly `setxkbmap -layout de` once; only proceed to XTEST after server XKB and client core-map evidence both confirm the German transition. Run backend preflight on `=B2*A2€`, require zero emissions and zero receiver keypresses, then send `=B2*A2` once through `X11Backend.text`. Record server dumps, keymaps, xev/XLookupString events, process lifetimes and hashes.
- **D — decision:** `PASS_GERMAN_XKB_TEXT_DELIVERY_SCOPED` only if all three German rows and the US control decode exactly `=B2*A2`; German server/core maps change from US to de; the frozen candidate plan matches each active map's level 0/1; all planned press/release events match the receiver trace; and the unsupported payload refuses with zero emissions/events. A wrong/missing/extra character or emitted key event on unsupported preflight is `FAIL_GERMAN_XKB_TEXT_DELIVERY`. XKB extension, baseline, layout-application, source, image, runner, audit, timeout, or integrity problems are `STOP/HOLD` and never a semantic pass/fail. The frozen independent auditor must verify all rows, source/artifact hashes, and reject the preregistered in-memory corruption challenges.
- **C — constraints:** OrbStack Docker Engine 29.4.0, Linux/arm64; image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`. Container runs with `--network none`, read-only root/source/harness, a private `/tmp`, and only a dedicated result mount writable. It starts private Xvfb servers with XKEYBOARD and XTEST. No host display, host input, physical keyboard, GUI application, application data, Calc, MCP, model, network request, image pull, package install, or production change. A pre-freeze construction deviation is explicitly retained in `CONSTRUCTION-NOTES.md` and excluded from formal results.
- **U — limits:** Standard two-level German XKB and this exact current-main X11 backend under private Xvfb only. No Calc/API/MCP task effect, actual German hardware keyboard, level-3/Compose/dead-key/IME behavior, other layouts/backends, human-tempo/latency benefit, or product claim.

## Frozen source and environment

- Repository: `Unjuno/agent-interface`.
- Main source base: `eca4bcc1ee839b80442397e27f238c97d6dd6bb4`.
- Candidate path: `runtime/backends/x11_v1/backend.py`; Git blob `9cae101a219348077668c8fc086acf8e13154afe`; file SHA-256 `3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8`.
- Runtime import closure: the 17 Python files under `runtime/backends/x11_v1/` and `runtime/core_v1/`, individually frozen in `source_manifest.json`; directory tree blobs `0a497398c7fd0dabbf75565f4be02eb24f6b0664` and `1209a89e04eb820d6be7dd3f3390adb07d0d3afc`.
- Image immutable local RepoDigest/config ID: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64. Entrypoint must be overridden to `python3`.
- Construction observed Python 3.12.3, setxkbmap 1.3.4, xkbcomp 1.4.6, Python-Xlib 0.33, Xvfb, xev and stdbuf. The formal runner records the actual runtime versions and extension checks.
- Runner and independent auditor are frozen by this preregistration commit. Their SHA-256 values are included below before formal execution.

## One-shot formal command

Run from the repository root after pushing this preregistration commit. Before invocation verify that `results/formal-01/` is empty and that the image reference resolves to the frozen ID above. Do not pull or rebuild the image.

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD/runtime:/src/runtime:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v1:/harness:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v1/results/formal-01:/out:rw" \
  -e PYTHONPATH=/src \
  --entrypoint python3 \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/run.py /out
```

Independent audit must run in a second fresh container with `--network none`, read-only root, runtime and formal result mounts, and only `results/independent-01/` writable. It uses the already-frozen image and `audit.py`; it must not import candidate code or modify formal raw bytes. Formal and audit Docker stdout/stderr, exit codes, image inspections, raw bytes and all hashes are retained.

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 64 \
  --tmpfs /tmp:rw,nosuid,nodev,size=32m \
  -v "$PWD/runtime:/src/runtime:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v1:/harness:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v1/results/formal-01:/formal:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v1/results/independent-01:/audit:rw" \
  -e PYTHONPATH=/src \
  --entrypoint python3 \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/audit.py /formal /audit
```

## Frozen code hashes

- `source_manifest.json` SHA-256: `b23c3ae2dce161fa89bc6a64cd8db7ad529a6353683d42a758d2e5def15b9b69`.
- `run.py` SHA-256: `ab3e1578b86869b5a891a9615b79499f83fdb3361ccc3c4dc8cf13da268fd466`.
- `audit.py` SHA-256: `f325d4ebf24d5c30740ef03b1f7b3b1f0356296bf5ab5c496a141e3f6e80fdb3`.
