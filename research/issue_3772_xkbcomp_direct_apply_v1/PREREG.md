# Issue #3772 — direct xkbcomp server-apply diagnostic

## H / T / D / C / U

- **H:** `setxkbmap` produces a valid German keymap but its application path leaves the active Xvfb US. Feeding the exact generated keymap to the image's existing `xkbcomp` targeting the same display may make XKB state active.
- **T:** Allocation `issue3733-german-xkb-xkbcomp-apply-formal-01`; a fresh German Xvfb row and US control. Save before query/server dump/fresh Xlib map. Generate exact source via `setxkbmap -display :N -print -layout de`, retain it, apply once with `xkbcomp -w 0 - :N` and captured stdin, then query/dump/new-client map. Stop after the first failed gate. No candidate import, XTEST input, or package install. Independently audit all raw artifacts.
- **D:** PASS_DIAGNOSTIC only if direct apply return succeeds and active query confirms German, server dump and fresh-client map are retained, US control is untouched, processes are reaped and independent hashes pass. Otherwise STOP with exact layer; command success alone is insufficient.
- **C:** OrbStack Linux/arm64; pinned image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, network none, read-only root/harness, dedicated empty formal output mount; host logs separately. No UI/host display, runtime candidate, physical input or package changes.
- **U:** Private Xvfb/XKB server state only; no text-delivery or product claim.

## Frozen code and one-shot command

Only image-confirmed Python-Xlib, Xvfb, setxkbmap, and xkbcomp are used. Runner/auditor are hashed below. Verify formal/audit output directories empty. Never rerun a populated allocation.

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 96 \
  --tmpfs /tmp:rw,nosuid,nodev,size=32m \
  -v "$PWD/research/issue_3772_xkbcomp_direct_apply_v1:/harness:ro" \
  -v "$PWD/research/issue_3772_xkbcomp_direct_apply_v1/results/formal-01:/out:rw" \
  --entrypoint python3 agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/run.py /out
```

Independent audit is a second fresh no-network container: `/harness/audit.py /formal /audit`, where formal is read-only and only `results/independent-01/` is writable.

- `run.py` SHA-256: `a0d8a53fb78c91406fcd666c5012578943ff3f08aefb12ba5da3f75543f87aa1`
- `audit.py` SHA-256: `e88dc45e8eb7dbe38ceb71a7ee0ac3cf01be9c87a718285087d470ca6b8f2b97`
