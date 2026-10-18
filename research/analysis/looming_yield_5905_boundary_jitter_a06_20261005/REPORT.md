# Issue #8112 A06 — boundary-jitter robustness result

**Disposition: `NO_INCREMENTAL_VALUE` (synthetic, method-scoped).** The frozen
success condition required secant TTC to strictly exceed *both* simple visual
cue frontiers at one or more matched false-YIELD budgets. It did not: at every
budget 0–6, TTC, pixel-change, and relative-area-growth each reached 24/24
approach detections. This finite assay therefore found no incremental TTC
advantage; it does not prove equivalence outside this fixture.

## H / T / D / C / U

- **H:** Independently randomized ±1–3 px apparent-radius boundary jitter can
  reduce or eliminate secant-TTC's early-contact detection advantage over
  pixel-change and relative-area-growth at matched false-YIELD budgets.
- **T:** Seed `20261014`; 36 opaque-ID 256×256 PGM sequences, 5 irregularly
  sampled frames each; 24 approach sequences (six at each jitter amplitude
  0–3 px) and 12 controls. Candidate emitted 36 rows; 30 were eligible and 6
  were rejected for the frozen visible-area-loss, track-change, or timestamp
  gates. Candidate received no truth/jitter labels.
- **D:** Raw reconstruction `PASS`; auditor rejected timestamp- and
  track-substitution mutations. Across false-YIELD budgets 0–6, all three
  methods had best true-positive count 24/24; no budget met strict TTC
  superiority. The recorded decision is `NO_INCREMENTAL_VALUE`.
- **C:** Integer rasterization, these thresholds and sample times, and the
  finite control mix constrain the comparison; this does not establish that
  cues are generally interchangeable.
- **U:** No real optics/tracking, DOOM, GUI, model latency, task effect, input
  release, recovery, survival, or safety was tested. Synthetic pixel jitter is
  not a calibrated sensor-noise model.

## Frozen execution provenance

- Allocation: `UNJUNO-8112-BOUNDARY-JITTER-A06-ORBSTACK-20261005`.
- Main base: `19a6b723e58ccfd2b8265e88659589ef9223fcc9`.
- Image: `python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151`
  (`linux/arm64`, Python 3.14.8; cached, no pull).
- Engine: OrbStack Docker; network disabled, read-only rootfs, one CPU requested,
  memory limit requested (enforcement not independently asserted), candidate
  had no truth mount, and candidate/auditor output mounts were separate.
- Invocations: candidate 1/1 exit 0; auditor 1/1 exit 0; retries 0. No formal
  rerun is authorized or included in CI.
- Runner stdout reports `eligible=30`, `rows=36`; auditor reports
  `case_count=36`, `raw_reconstruction=PASS` and `NO_INCREMENTAL_VALUE`.
- Candidate output SHA-256:
  `9178cd939156ea29bd30264b5993537d6f5291943e76861f2fb12ad0827055ca`.
- Audit output SHA-256:
  `78f7841e3dd00c68733394f0210ed9cc8675b92caa95ba614f3166b4228ec993`.
- A06 freshly pins the actual current-main A09 role bytes; it does not claim
  identity with the discrepant historical A09 hash metadata. See `FROZEN.json`
  for source/frame hashes, and `RUN_RECORD.json` for exact commands and exits.

## Successor lineage

Prior allocations remain immutable: A01/A02/A03 stopped on exact-main gates;
A04's single candidate/auditor pair ended in `FAIL_INTEGRITY_AUDITOR_INPUT_SCHEMA`;
A05 stopped before freeze when main advanced. A06 used a new seed and corrected
the auditor's truth-list envelope; it did not replay any predecessor allocation.
