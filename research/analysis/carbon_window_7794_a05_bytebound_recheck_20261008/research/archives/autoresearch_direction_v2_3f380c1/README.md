# Historical autoresearch direction v2 transport failure

**Status: archived `FAIL_MEASUREMENT_INTEGRITY`; not a promoted experiment or runnable current-main entry point.**

This directory preserves the complete six-file final experiment directory from commit `3f380c19ecb1aa144d1b1f1e9e0ee588c1cf8110` on `research/autoresearch-direction-v2-6dfe55d`. The original path was `research/doom/autoresearch_direction_v2/`. All six files reuse the original Git blobs; this README is the only newly authored record.

## Retained observation and limits

`FAILURE.json` reports one session started, zero completed formal cases and zero measured actions submitted. The recorded failure is a controller-clock handshake timeout before policy input. The record attributes it to mixing descriptor-level `select()` readiness with buffered text reads. This maintenance operation preserves that reported diagnosis; it does not independently rerun or verify the absent raw logs.

No policy efficacy, MAP01 completion, performance or production capability follows from this failure. The raw-log SHA-256 references in `FAILURE.json` are references, not proof that those log bytes are present in this snapshot. The frozen runtime and fixture dependencies in `FREEZE.json` remain required for any historical reconstruction.

## Why a separate archive

The source branch also deletes/replaces the earlier v2 fixtures and preregistration retained on main through PR #133. Importing that branch wholesale would discard the earlier record. This archive preserves the failed later snapshot without changing any existing v2 file, workflow, runtime or release ref.

The five-file v3 transport-repair precursor is already retained at `research/doom/autoresearch_direction_v3/` through PR #142; it was verified blob-identical to source commit `ff4177a2a62eb1e4bf2292b3f3c40277134a01cd` during this maintenance pass. A v3 freeze is not a completed formal result.

## Identity

| File | Original Git blob SHA-1 |
| --- | --- |
| CONSTRUCTION.json | ae0cebaa2a848d38c670d74d0cea45c01193ac47 |
| FAILURE.json | bb8f2ccaa82e42be049c11d6f0a6a023801d83ab |
| FREEZE.json | 9244a1be623ab66c3ddd158e8a023cf270d395d7 |
| preregistration.json | 8f6ecf40d2dee2dd2efd05604f122e75fe1d23fa |
| runner.py | c50f1327199e2b3b837a56a2eab56f3df095ef23 |
| test_runner.py | 71f28ad528d3d548c355bddcc60023e7c0c71948 |

Do not edit the archived files or rerun the failed allocation in place. A new experiment requires a new allocation and freeze. Archiving final file content does not by itself prove that all intermediate commit history can be deleted.
