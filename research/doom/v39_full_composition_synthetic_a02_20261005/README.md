# V39 full-composition synthetic reproduction A02

## H/T/D/C/U

- **H:** The frozen V39 → V15 → V12 → V13 Executor → typed backend → owner source bundle can reproduce one bounded synthetic decision with reconciled typed/full observations and empty simulated input state after release.
- **T:** Re-run the archived A01 candidate once using its exact 68-file source manifest, then independently audit the new raw output. No model, live game, OS input, or allocation is used.
- **D:** `PASS_CONSTRUCTION_SCOPED` requires one admission/release pair, five typed/full observation matches, fake-X KeyPress then KeyRelease, empty final fake keymap, non-authoritative physical-verification flag, empty stderr, and `map_exit=false`/`player_dead=false`.
- **C:** This tests source composition under fake game, planner, capture, and Xlib seams only. It is not a current-main integrated run: the bundle records origin main `24cbb631b972eee1723d2372adf53032dfdaab20` and PR #8094 head `88e8099de97de12c29fcf3db0cb374b160a27ead`.
- **U:** No live threat exposure, physical actuation, application consumption/effect, recovery efficacy, death/survival benefit, or MAP01 completion is established. Current main has advanced to `60aff39f60defd06f9b4cabd0941e54d17c570df`; this run does not validate that newer source closure.

## Execution

- Python 3.12.13, Pillow 12.3.0, NumPy 2.5.3, macOS arm64 host; temporary venv.
- Candidate command: `V39_SYNTHETIC_SOURCE_ROOT=<candidate-source> V39_SYNTHETIC_WORK=<fresh-dir> PYTHONPATH=<reproducer-and-source-paths> V39_FAKE_X_TRACE=<fresh-trace> python3.12 reproducer/run_full_v39_v15_synthetic.py`.
- Candidate result: `PASS_CONSTRUCTION_SCOPED`, one iteration, 28 events, one key-release receipt, final fake-server keys empty; model wall 0.000470 s (fake planner); post-control score: `map_exit=false`, `episode_finished=false`, `player_dead=false`, `kill_count=0`, `reward=0`.
- Independent audit: 68 source SHA/blob identities matched; five typed/full observation pairs reconciled; one input admission and one release; fake-X edges were KeyPress→KeyRelease and final key set empty; non-authoritative measurement and synthetic limitation checks passed.
- The repository's audit script expects archived paths under `raw/run/...`; the fresh run was copied into that layout before auditing. The frozen A01 files were not modified.

Raw candidate artifacts, source bundle, fixture and fake-X trace are in this directory. The candidate was re-executed only as a construction reproducibility check, not as the unresolved Issue #59 live experiment.
