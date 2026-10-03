# Archival qualification: pre-run source-hash STOP

This is a recovery copy of the preparation package at original branch tip `24c089a31fa7f48fb54a00acfb61a871d38a1c25` (`research/service-fairness-6613-t0-hostcpu-20261002`). Its nine original files are preserved byte-for-byte. This additive qualification explains the predecessor STOP and limitations of the retained preparation package; it is not an experiment result and is not a runnable allocation.

## H / T / D / C / U

- **H:** No hypothesis disposition is available from this allocation. The frozen source identity gate failed before formal execution.
- **T:** The original `FREEZE.json`, README, candidate/auditor sources, fixtures, runners, and construction tests are preserved byte-for-byte. No candidate, formal auditor, retry, or result-output generation was performed during this archival recovery.
- **D:** `STOP_PREREGISTRATION_HASH_MISMATCH`. Of the eight entries in `FREEZE.json.sha256`, seven source hashes reproduce. `candidate.py` does not: frozen expected SHA-256 `4de0d746b2d242b22e8946ffa9318e2f13de298b4db2c6097bbeef982f8882bf`; original branch bytes SHA-256 `774876c0f0b8aca401fc2f65c7a75a0e1618accbf7dcf8338a916d8c6b4e7505`. The original package contains no `candidate_raw.json` or `audit.json`.
- **C:** The source/freeze identity inconsistency stopped formal execution. Separate preparation defects and inconsistent provenance are preserved below. Neither the STOP nor the source-only review determines which candidate version was intended or establishes a policy outcome.
- **U:** No PASS/FAIL hypothesis result, service fairness, human, GUI, authority, safety, or product claim follows. Do not repair this freeze or run it as a retry. The later service-debt A01 and EDF allocations are distinct successors with their own preserved outcomes; do not pool them with this STOP.

The source files other than this qualification are copied unchanged from the original branch. The related Issue #6613 records the predecessor `STOP_PREREGISTRATION_HASH_MISMATCH` and the later distinct allocations.

## Retained execution wording and provenance

The original [README](README.md#execution-and-scope) says the simulator "ran once" and presents candidate/auditor commands. That statement is stale preparation text, not evidence of a formal invocation. [Issue #6613's terminal allocation record](https://github.com/Unjuno/agent-interface/issues/6613) states that preflight stopped before the candidate was invoked and that no formal candidate/auditor rerun or repair was attempted. Original formal invocation counts are **candidate 0, auditor 0, retries 0**; both formal outputs were absent. Passing inline construction tests do not change those counts. The preserved commands do not authorize execution of this stopped allocation.

The Issue's committed allocation note names main `afea9a530cafd7af529df4c9e59f36b816bca24f`, whereas [FREEZE.json](FREEZE.json) and [candidate.py](candidate.py) name `8dc482223d2d1f6d4a54008b15070ed85f59447f`. The Issue explicitly records this branch/base/source provenance inconsistency alongside the candidate hash mismatch. This archive preserves both identifiers without choosing or correcting the intended base.

## Separate auditor/fixture case-ID mismatch

The preserved [formal fixture](fixture_public.json) names its asymmetric case `fresh_asym_07` and its release-control case `fresh_controls_07`. The [auditor](audit.py) selects `asymmetric_repeated_contention` for its asymmetric comparison (line 184) and `eligibility_and_release_controls` for its additional release-order check (line 197). Those names occur in the inline construction fixture in [test_method.py](test_method.py), but are absent from the formal fixture.

By inspection of these predicates, the asymmetric selection is empty for the frozen formal case IDs, so the auditor would append `ASYMMETRIC_ROWS_MISSING` even for otherwise matching replay rows. Its additional release-order loop selects no formal rows. This does not mean release evidence is wholly unchecked: the independent full-trace comparison at line 163 still compares events. Passing construction tests with different case IDs cannot establish these two formal selectors' coverage.

This is a separate preserved preparation defect, established by static source inspection. No formal fixture replay, candidate invocation, or formal auditor invocation was performed to establish it; no counterfactual audit output or scientific FAIL is claimed. The original candidate, auditor, fixture, README, freeze and STOP remain preserved, and any future corrected study requires its own authorized allocation and prospective freeze.
