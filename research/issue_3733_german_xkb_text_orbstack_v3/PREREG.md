# Issue #3779 — formal-03: German XKB formula delivery with persistent Xvfb state

## H / T / D / C / U

- **H:** The previous active-layout failures were caused by Xvfb resetting after the last client disconnected. Xvfb's pinned-image help documents `-noreset` as preventing that reset. With this mode fixed, the current-main X11 text planner may still incorrectly resolve German `=`/`*`; the private receiver provides the actual decisive test. Late unsupported `€` must fail before any key event.
- **T:** One allocation `issue3733-german-xkb-text-orbstack-formal-03-retry1`, current main `4b2e84b79633281138b6f72c70e98d5fe9a5bf95`, candidate blob `9cae101a219348077668c8fc086acf8e13154afe`. Retry-0 (`formal-03`) failed before producing raw results because `run_case` omitted `return row`; preserve its partial logs under `results/failed-formal-03-buildbug/` and do not reuse its output. Four distinct fresh Xvfb servers: three baseline-US→German rows and one untouched US control. All servers use `-noreset`; a private xev receiver starts before each layout transition. Each German row invokes `setxkbmap -layout de` exactly once. Proceed only after query says `de` and the server XKB dump changes. Capture baseline, after-transition fresh-client map, exact candidate plan, unsupported-preflight emissions/events, and if preflight permits, one `=B2*A2` XTEST emission with exact XLookupString and press/release trace. A confirmed-German planner rejection is candidate FAIL, not environment STOP; continue the remaining rows. Stop only on setup/integrity/receiver failures. Independent auditor runs in a second container.
- **D:** `PASS_GERMAN_XKB_TEXT_DELIVERY_SCOPED` only if all three German rows and US control produce exactly `=B2*A2`; Germany is server-verified; candidate chords match the measured event/keycode trace; all KeyPress/KeyRelease pairs complete; unsupported trailing `€` is refused with zero emissions and receiver presses; all four rows/artifact/source hashes verify independently. Wrong plan, text, trace, release count, or unsupported emission/refusal is FAIL. Image/source/setup/receiver/audit-integrity problems are STOP/HOLD, never PASS.
- **C:** OrbStack Docker Engine 29.4.0, Linux/arm64; immutable image `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`; network none; read-only root, runtime and harness; only `results/formal-03/` writable in the formal invocation. Host logs live under `results/host/` outside the harness and formal output mounts. No host display/input, GUI app, package install, network, model, Calc, source modification or replay of predecessor allocations.
- **U:** Exact candidate blob, standard two-level German XKB and this pinned private-Xvfb setup only. No task-effect, actual hardware keyboard, dead-key/Compose/IME/level-3, other layouts/backends, performance or product claim.

## Candidate/environment freeze

- Repository: `Unjuno/agent-interface`.
- Main source base: `4b2e84b79633281138b6f72c70e98d5fe9a5bf95`.
- Candidate: `runtime/backends/x11_v1/backend.py`, Git blob `9cae101a219348077668c8fc086acf8e13154afe`; file SHA-256 `3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8`.
- The 17-file runtime import closure and its per-file SHA values are pinned in `source_manifest.json`.
- The image is already cached and pinned by immutable digest; do not pull or rebuild.
- Runner/auditor and this prereg are frozen before formal invocation. Each formal and independent-audit output directory must be empty. Never rerun a populated allocation.
- Retry-0 setup failure is preserved byte-for-byte; its host log records `TypeError: 'NoneType' object is not subscriptable` after the first German map was successfully applied and independently visible in the server query/dump. No candidate formula key was emitted in that failed attempt.

## Formal one-shot command

```sh
docker --context orbstack run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 128 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD/runtime:/src/runtime:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v3:/harness:ro" \
  -v "$PWD/research/issue_3733_german_xkb_text_orbstack_v3/results/formal-03:/out:rw" \
  -e PYTHONPATH=/src --entrypoint python3 \
  agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27 \
  /harness/run.py /out
```

The independent audit is a second fresh no-network container, with runtime, harness and formal results read-only and only `results/independent-03/` writable; invoke `/harness/audit.py /formal /audit`. Preserve exact host logs separately. Never overwrite a formal invocation log with a retry.

## Frozen hashes

- `run.py` SHA-256: `2f95d7e117d4fbf064da384f1e40ac6688991e922a0496dff0bccea8a9199099`
- `audit.py` SHA-256: `399c46203b8b644e8f03cf1cdf31a91c4ea37addfe202b66b26684998041547a`
- `source_manifest.json` SHA-256: `097f9faf4072d6bf511be618c67984cb7a7f9dce804062364813d2879d9a3dd8`
