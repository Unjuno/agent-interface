# A05 H / T / D / C / U — exploratory only, not preregistered

This screen was run after current `main` revealed an A04 unregistered host pilot. It tests a different estimator but was not frozen as a formal allocation and did not run in a container. Treat it as exploratory evidence only.

**H:** Fitting apparent target radius across all five timestamped frames by ordinary least squares should reduce the last-interval raster-quantization error and cue more constant-approach cases than a two-frame secant estimate, without false YIELD on the six identifiable controls.

**T:** The immutable A03 fixture has 13 sequences of five 128×128 PGM frames at 100 ms cadence. The host probe uses the existing shape/track/time/background-scale gate; for eligible sequences it computes `TTC = final equivalent radius / OLS(radius-vs-time slope)`. It compares fixed TTC thresholds [1.5, 2, 2.5, 2.8, 3, 4] seconds against the existing pixel-change and area-growth grids, with 0.20 s release latency. Hidden contact labels are used only by the scorer/auditor. The animation twin is excluded from the six identifiable-control false-YIELD budget and checked for identical semantic output.

**D:** This screen shows a preliminary signal only if all six approaches cue with positive analytic release lead, no identifiable control cues, the twin matches, and OLS TTC's maximum true positives at FP=0 strictly exceed both pixel and growth baselines. Otherwise `NO_INCREMENTAL_VALUE` or a gate failure is reported. The independent raw-PGM auditor must reconstruct 13 sequences with zero errors. No result promotes beyond this exact finite fixture.

**C:** One fixed synthetic raster corpus, six positive and six identifiable controls; FP=0 is not a population rate. The comparison does not measure capture cost, UI latency, physical cancellation, task progress, or performance under held-out scenes.

**U:** Host-side, unregistered screen because the isolated OrbStack guest's nested OCI runtime denied required BPF/cgroup and device-node setup. No container or formal allocation ran. No inference about gameplay, agent behavior, safety, live-control authority, or general TTC reliability. A no-cue result never implies safe continuation.
