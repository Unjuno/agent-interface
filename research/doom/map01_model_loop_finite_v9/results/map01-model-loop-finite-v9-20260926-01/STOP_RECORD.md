# v9 formal allocation result — seed 990635

Classification: **`HOLD_INFRASTRUCTURE_HOST_LEASE_MARGIN_BELOW_5S`**. The allocation was launched once and is permanently consumed. No retry was made.

## H/T/D/C/U

- **H:** With the exact WAD restored and hash-bound HUD readers, the frozen submit-send controller can enter a fresh MAP01 session and admit multiple bounded model-authored actions. This allocation did enter gameplay and admitted two actions, but it stopped before the preregistered 24 decisions; the full hypothesis is therefore unresolved.
- **T:** One pinned OrbStack run, seed `990635`, fresh Freedoom MAP01, skill 1, ViZDoom 1.3.0 at 35 tics/s, up to 24 decisions, `gpt-5.6-luna`/low, session span 4, read-only/no-network runtime image.
- **D:** The frozen 5-second host-lease-margin guard fired while translating a later submit. This is an infrastructure HOLD, not gameplay FAIL. No 24-decision result or independent terminal score exists.
- **C:** Issue [#4484](https://github.com/Unjuno/agent-interface/issues/4484) preregistered this one-time seed and output path. The current-main source manifest matched all 20 frozen source files before launch and in the post-run audit. WAD SHA-256 matched the pin. Prior v1-v8 allocations remain unchanged. Seed and output path must not be reused. The #4484 body printed a malformed 63-character effective-controller digest ending in `...aab3`; the frozen v7 record and generated effective source contain the valid 64-character digest ending in `...aab3a`. The adapter/source set used was frozen and matches those correct identities; preserve the issue-body typo rather than silently rewriting history.
- **U:** Whether the controller sustains a full finite horizon under the current timing/lease policy; whether the two admitted actions improve task progress; and whether MAP01 can be exited remain unknown.

## Observed result

- Formal invocation started exactly once with the command frozen in Issue #4484.
- The container started with image `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e` (`linux/arm64`), `--network none`, read-only root, bounded tmpfs, read-only source mount, and additive output mount.
- Environment record: fresh MAP01, skill 1, ViZDoom `1.3.0`, 35 tics/s, seed `990635`, no fixture, IWAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- Planner protocol: 315 rows; two completed model turns and two valid model answers. Both model-authored commands produced completed action programs: `forward` and `use`. This confirms entry to the live model-in-loop task and more than one admitted action for this allocation only.
- Runtime: 151 exact observations and 151 typed observations; 3 physical input admissions (`Up`, `Shift_L`, `e`); 8 accepted programs, including clock/cover/plan programs.
- All 9 owner-release records independently report verified empty `keys_down` and `buttons_down`, including final owner close.
- Stop: adapter raised `RuntimeError: HOLD_INFRASTRUCTURE: host lease margin below 5s` at the frozen send-translation guard (`research/doom/map01_model_loop_finite_v7/preflight/effective-controller.py:601`). `runner-exception.txt` preserves the traceback with machine-specific checkout paths normalized.
- Trigger path is reproduced from the frozen source: the second model answer requested `use` with a `no_visible_effect` contingency; `refresh_between_segments` sends an observe-only lease with exactly 5 seconds (`map01_overlap_controller_v39.py:1074-1076`); `_LeaseClockStdin.write` performs three clock probes and then requires at least 5 seconds to remain (`effective-controller.py:583-601`). Thus the refresh's exact 5-second deadline is incompatible with the strict post-probe 5-second minimum. The exception occurred on this contingency refresh, before fallback input was sent. The machine-readable audit checks both source predicates.
- `report.json` and `runtime/score.json` are absent because the controller stopped before finalization. Do not infer map exit, no-exit, death, or gameplay failure from this partial allocation.
- Read-only audit: `V9_STOP_AUDIT.json`; audit source: `research/doom/map01_model_loop_finite_v9/audit_stop.py`.
- Local pinned-container regression: 5 existing tests passed (2 v39 controller tests; 3 v3 HUD/typed-observation tests) with the frozen hash-bound WAD mounted read-only. The first test invocation could not collect on host Python due missing Pillow; a first container attempt also had a missing read-only mountpoint. The corrected isolated invocation passed all 5 tests.

## Raw evidence integrity

`V9_STOP_AUDIT.json` contains SHA-256 hashes for every retained raw file (322 files, 24,710,371 bytes at audit time), as well as event counts, the 5-second source-conflict check, and source-manifest verification. Key hashes:

| Artifact | SHA-256 |
|---|---|
| `planner-protocol.jsonl` | `89138edac451c3c1ba89422b499137cf51d505100ff28734adee334c178a12ca` |
| `runtime/events.jsonl` | `9de9fd9d09ed49ff6d088060301413b12381a8826bbb1c83687974933bec4a24` |
| `runtime/owner-events.json` | `370c9af56777b9d8ffb6d32b8dbfa0d1f5bb3bf35e6c3765d6480aee9043761c` |
| `runner-exception.txt` | `3526f5ef905fc0bffb921a4f480f6647139cfaa130e2c375c7b480953e29d7b0` |
| `V9_STOP_AUDIT.json` | `40e1a7245c60d289b34af601ca1acfd3cbdd55ac666f6bf240ee745d38a772a8` |

## Next experiment boundary

Keep this result immutable. A successor should target the host-lease timing failure (not repeat seed `990635`): isolate why a valid action reaches the 5-second margin guard after two admitted actions, freeze any changed timing/lease hypothesis and gates in a new Issue, and allocate a new seed/output path only after fresh collision and resource checks. Preserve the existing validity, freshness, bounded-input, and release gates.
