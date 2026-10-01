# MAP01 model-loop finite v9

This folder preserves one formal experiment preregistered as [Issue #4484](https://github.com/Unjuno/agent-interface/issues/4484). The primary objective was to test the posted guarded-controller idea in a live MAP01 episode, not to change branches or integrate code.

## Result

The run entered a fresh Freedoom MAP01 session, completed two valid model turns, and admitted/completed two model-authored actions (`forward`, `use`). It then stopped with **`HOLD_INFRASTRUCTURE_HOST_LEASE_MARGIN_BELOW_5S`** before the frozen 24-decision horizon. All nine recorded physical input releases verified empty. No final score exists, so this is neither a finite-clear PASS nor a gameplay FAIL.

The immediate cause is a conflicting time contract on the second answer's no-visible-effect contingency path: `refresh_between_segments` submits an observe-only command with a 5-second deadline, while the frozen send wrapper performs three clock probes and requires at least 5 seconds still remaining before sending. The guard therefore stops before sending the fallback. A separate preregistration typo is retained: Issue #4484 printed a 63-character effective-controller digest; the frozen/generated SHA-256 is the 64-character value ending in `...aab3a`. The executed adapter and its 20 runtime inputs match the frozen source identities.

The formal allocation and machine-readable audit are immutable evidence under `results/map01-model-loop-finite-v9-20260926-01/`. See [STOP_RECORD.md](results/map01-model-loop-finite-v9-20260926-01/STOP_RECORD.md), [V9_STOP_AUDIT.json](results/map01-model-loop-finite-v9-20260926-01/V9_STOP_AUDIT.json), and the retained [planner protocol](results/map01-model-loop-finite-v9-20260926-01/planner-protocol.jsonl).

## Reproduction and validation

- [FORMAL_FREEZE.md](FORMAL_FREEZE.md) records the exact one-time command and environment. Do not rerun seed `990635` or reuse its output path.
- The minimal adapter chain used by that command is retained at `research/doom/map01_model_loop_finite_v3/adapter.py`, `...v5/adapter.py`, `...v6/adapter.py`, and `...v7/adapter.py`; the exact generated v7 controller is retained at `research/doom/map01_model_loop_finite_v9/frozen-source/effective-controller.py`.
- Read-only audit: `env PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/map01_model_loop_finite_v9/audit_stop.py`.
- Focused regression in the pinned image: 5 existing tests passed (2 v39 controller tests and 3 HUD/typed-observation tests) with the exact hash-bound WAD mounted read-only. The run used `--network none` and a read-only root. Audit the formal result separately; regression PASS is not an experiment PASS.
- Re-run those tests by setting `FREEDOOM_WAD` to a local file whose SHA-256 is the frozen IWAD hash, then running this from a full checkout:

  ```sh
  docker --context orbstack run --rm --platform linux/arm64 --network none --read-only --workdir /src \
    --tmpfs /tmp:rw,nosuid,nodev,size=128m -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$PWD":/src:ro -v "$FREEDOOM_WAD":/tmp/freedoom2.wad:ro \
    --entrypoint python3 issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e \
    -B -c 'import sys,unittest; from pathlib import Path; sys.path.insert(0,"/src"); import research.doom.test_doom_hud_signal_v3 as hud; import research.doom.test_map01_overlap_controller_v39 as ctrl; hud.WAD=Path("/tmp/freedoom2.wad"); suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(ctrl),unittest.defaultTestLoader.loadTestsFromModule(hud)]); result=unittest.TextTestRunner(verbosity=2).run(suite); raise SystemExit(not result.wasSuccessful())'
  ```
- The pinned container did not generate a final gameplay score because the run stopped at the lease guard. The adapter timing conflict should be corrected and tested under a separately preregistered successor Issue, new seed, and new output path; preserve freshness, bounded input, and release gates.

## Integration scope

This PR publishes the experiment, STOP/HOLD reason, and reproducible audit inputs. It does not claim an integrated runtime success or modify the controller policy. An integration worker should independently review and, if desired, run the distinct successor hypothesis.
