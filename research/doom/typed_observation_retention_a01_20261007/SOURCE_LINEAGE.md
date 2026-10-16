# Source lineage and rescue qualification

- Source pull request: #8258; source branch: `research/59-typed-observation-retention-a01-20261007`.
- Source head: `9a714b0ce5568f98022dc455754b0019315eb03c`; pinned source commit/base: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- The nine files in the original package were byte-identical to the source branch before this lineage record was added. All eight entries in `PACKAGE_MANIFEST.json` verify.
- The saved-data-only independent audit passed: two retained rows, five of five mutations rejected, and all package hashes accepted. The candidate was not rerun; its first path-error STOP and subsequent retained pass remain as originally recorded.
- Current-main qualification at rescue: three of the five frozen source files still match their recorded SHA-256; `map01_overlap_controller_v39.py` and `doom_typed_observation_v1.py` differ. Therefore the retained construction result is historical evidence for the frozen snapshot, not a current-main source validation. The exact session sink and typed backend files do still match.
- No live game, model, GUI, X11, input, Docker, GPU, or formal #59 allocation was run. This proves persistence for supplied synthetic rows and static ordering only; it does not prove live signal capture, monitor behavior, cancellation, release, recovery, or task effect. Issue #59's live lane remains open.
- Source PR #8258 was a draft with no review submissions at intake. This rescue adds custody/context without rewriting its original artifacts or promoting its result.
