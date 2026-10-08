# MAP01 attack-onset phase — allocation 03

Issue: [#4223](https://github.com/Unjuno/agent-interface/issues/4223)

This separate allocation preserves all earlier outcomes. Its only operational change is a fresh local Docker Desktop image built from the exact pinned Python base image and the issue's verified offline wheel set; the new image identity is frozen before any formal session. No GitHub Actions run is part of this experiment.

Read `PLAN.md` for H/T/D/C/U, `ENVIRONMENT.json` for the built image and runtime, `FREEZE.json` for immutable source/allocation identities, and `RESULT.md`/`AUDIT.json` for the eventual outcome. Raw per-session controller events, runtime traces and scorer samples are retained under `results/formal/`. The six experiment source files in `source/` are the exact source capsule; `dependencies/v12/` contains its hash-manifested measurement owner inputs. `inputs/runtime-source.tar.gz` is the exact offline runtime source archive; its manifest is `inputs/runtime-artifact-manifest.json`.

The 80 MB offline runtime-artifact ZIP is kept in the local scratch area and is not committed. Its artifact ID, whole-archive SHA-256, and each wheel SHA-256 are recorded by the artifact manifest and `ENVIRONMENT.json`. Formal containers use `--network none`, read-only source mounts, and bounded writable `/tmp` and results mounts.

Scope is the fixed seed/fixture and the two onset delays in `PLAN.md`; this is not an independent-map or general-policy result.
