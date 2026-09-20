# Issue #3764 — German XKB server/client map diagnostic

## H / T / D / C / U

- **H:** The pinned private Xvfb environment reports German from `setxkbmap -query` and `xkbcomp` after one layout application, while the prior fresh Python-Xlib `get_keyboard_mapping` returned the US baseline map. Independently capture `xkbcomp`, `xmodmap -pke`, full Xlib core map, and selected Y/Z/equal/asterisk symbols to identify which representation changed.
- **T:** One allocation, `issue3733-german-xkb-map-diagnostic-formal-01`, two fresh Xvfb servers: German transition and untouched US control. Save raw stdout/stderr and structured maps. No Agent Interface candidate import, construction, or XTEST call. Run an independent audit in a second container.
- **D:** `PASS_DIAGNOSTIC_SCOPED` only when the German layout is observed, independent server/core map readers agree on actual changes, selected symbols change, control remains US, cleanup completes, all artifact hashes verify. Any disagreement or integrity/setup problem is STOP; this diagnostic alone is not a candidate result.
- **C:** OrbStack Linux/arm64; image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, network none, read-only root and harness, dedicated empty output mount. Host logs are outside the output mount. No image pull, package install, host display/input, candidate, or XTEST event.
- **U:** Only Xvfb/XKB/Xlib representation behavior in this pinned image. No text delivery, application effect, hardware layout, or product claim.

## Frozen environment/source

Base main: `e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8`. Python 3.12.3, Python-Xlib 0.33, setxkbmap 1.3.4, xkbcomp 1.4.6 and xmodmap are available in the pinned image. Runner and audit hashes are recorded below; no runtime repository file is changed by this diagnostic.

## One-shot run

Before running, verify `results/formal-01/` and `results/independent-01/` are empty. Mount only those directories writable. Retain stdout/stderr logs separately in `results/host/`. Do not rerun if any formal artifact exists.

Formal:

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 96 \
  --tmpfs /tmp:rw,nosuid,nodev,size=32m \
  -v "$PWD/research/issue_3764_german_xkb_map_diagnostic_v1:/harness:ro" \
  -v "$PWD/research/issue_3764_german_xkb_map_diagnostic_v1/results/formal-01:/out:rw" \
  --entrypoint python3 agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/run.py /out
```

Independent audit uses a second fresh container, `/harness/audit.py /formal /audit`, with `/formal` read-only and only `results/independent-01/` writable.

## Frozen hashes

- `run.py` SHA-256: `8a816c7840607acde47ab3cf5a07696516f21b48193e5cded1ee087e2410da43`
- `audit.py` SHA-256: `48c51395ea1b556aaabeb3dfa80b3ce82be115aab250e3c606fa3cfac96ee107`
