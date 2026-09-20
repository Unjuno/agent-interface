# Issue #3770 — Xvfb setxkbmap target/rules diagnostic

## H / T / D / C / U

- **H:** Same image and `setxkbmap -layout de` produced contradictory observations. An explicit `-display :N` plus `-verbose 10`, `-print -verbose 10`, and a short delayed re-query will reveal target/rules/compiler behavior.
- **T:** Allocation `issue3733-german-xkb-apply-diagnostic-formal-01`; fresh German-transition and US-control Xvfb servers. Capture before query/rules/xkbcomp/Xlib, explicit target apply argv and stdout/stderr, print rules, delayed query/xkbcomp/Xlib, server log, cleanup and hashes. Stop after first setup/layout failure. Independent audit in a separate container.
- **D:** PASS_DIAGNOSTIC only if explicit-target German query and xkbcomp transition are established, required rules/compiler output is retained, Xlib snapshot is preserved, US control remains US, cleanup and independent hashes validate. Any missing evidence or unresolved transition is STOP. No candidate conclusion.
- **C:** OrbStack Linux/arm64; immutable image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`; network none; read-only root/harness; isolated writable formal output. Host logs are a separate path. No packages, candidate runtime, XTEST input, host UI, or replay.
- **U:** Private Xvfb layout application only; no German text delivery or task/product effect.

## Frozen environment and code

The image is pre-existing and already inspected. Only Python-Xlib, Xvfb, setxkbmap, and xkbcomp are used. Runner and auditor hashes below are fixed before the single formal invocation.

## Commands

Verify formal and audit output directories are empty. Mount only formal results at `/out` writable; keep container logs outside both `/harness` and `/out`. Never rerun a populated allocation.

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 96 \
  --tmpfs /tmp:rw,nosuid,nodev,size=32m \
  -v "$PWD/research/issue_3770_xvfb_layout_apply_diag_v1:/harness:ro" \
  -v "$PWD/research/issue_3770_xvfb_layout_apply_diag_v1/results/formal-01:/out:rw" \
  --entrypoint python3 agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/run.py /out
```

Independent audit: a separate fresh no-network container, `/harness/audit.py /formal /audit`, with formal results read-only and only `results/independent-01/` writable.

## Frozen hashes

- Runner SHA-256: `bbede65b30b03f7ce4db89a210edfc9e563689f4f15dad12bedd29c748897c8f`
- Auditor SHA-256: `07593700a4031dab309ae70b72e7bd186a016ebea4769be00f902a7ff6f252f9`
