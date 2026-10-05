# Issue #59 — current v39 controller pair-guard integration (A04 construction)

## H / T / D / C / U

**H.** A03 established paired-epoch validation in a standalone prototype. The current v39 controller must apply that boundary to fire-containing renewable covers, fail closed on missing, mismatched, out-of-order, or malformed epoch evidence, and deliver hard invalidation to the existing planner-admission path.

**T.** Freeze the current controller and focused regression suite. Run the new paired health/ammo controller tests plus the existing v39, source-refresh, and immediate action-validity contract tests. The cases cover coherent soft ammo change, zero-ammo invalidation and final-admission rejection, source and current-pair mismatch, boolean/float epoch aliases, out-of-order events, and health-only non-fire behavior.

**D.** PASS only if every focused regression passes and the changed Python files compile. This establishes controller construction/integration semantics only.

**C.** The suite uses synthetic observations and stubs. It does not test event delivery timing, real HUD extraction, keyboard release, cancellation races, or whether ammo change occurs during an actual fire cover. Fail-closed mismatches may interrupt recoverable cover.

**U.** Do not infer live safety, useful task progress, survival, verified empty release, or MAP01 completion. Any live matched run remains a separate gate and requires its own allocation and evidence.

## Runtime and source

The change is based on A03's source commit `e561b25b700680df4e6ffd2b92faf1dde1682ef7`; `origin/main` advanced to `b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3` during this work with the A03 construction record. A04 source hashes and runtime are frozen in `FREEZE.json`. Tests use CPython 3.14.5 with Pillow, NumPy, and python-xlib supplied through ephemeral `uv run --with` dependencies; no ViZDoom engine, game, GUI, or OS input was started.
