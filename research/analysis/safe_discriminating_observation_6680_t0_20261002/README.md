# Issue #6680 — finite safe-diagnosis/recovery policy comparison

This additive T0 tests one limited contrast: after a subthreshold residual alarm has already caused current actuator release, does one bounded read-only observation support better recovery decisions than fixed-reobserve/fixed-reset policies in identifiable synthetic worlds, while remaining UNKNOWN/YIELD on overlapping, unsupported, or ineligible evidence?

The hypothesis and stopping rules are frozen in [PREREGISTRATION.md](PREREGISTRATION.md). Candidate input is [fixture.json](fixture.json); hidden world/action truth is isolated in [oracle.json](oracle.json). `candidate.py` and `auditor.py` are separate standard-library implementations; the auditor reads the raw output and independent oracle. No runtime code or historical result is modified.

## Current disposition

**Preformal construction only; formal candidate/auditor/container counts are 0/0/0.** Construction tests are not an experimental result. One initial local construction suite failed, then the corrected suite passed 4/4; a host CLI smoke produced 20 rows and the local raw audit passed. These counts and the correction are in `CONSTRUCTION_LOG.md`. The proposed formal run requires an explicit bounded CPU/container slot and resolved shared-engine ownership. At freeze, two shared-engine containers and five other active OrbStack machines were visible; none was inspected internally, altered, stopped, or reused. WSLc is unavailable on this macOS host. Do not start a container based on this package alone.

The assay is deterministic and synthetic. Even a method-scoped PASS cannot establish real fault identifiability, safe recovery in a GUI, live control benefit, or authority.
