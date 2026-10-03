# Pre-formal record — S02 WSLc

## Current-main and collision review

- Intake main: `4d651bee9c89f0084afa6f8b9bea9cd6ac501757`.
- Refreshed main at construction freeze: `1644e5ded393ea472f48729df6f7d885a92f7837`.
- Compare: 16 commits / 95 changed paths since intake; none overlap Issue #5905/#6808, `looming_visual_assumption_gate_5905_*`, `ROADMAP.md`, or `docs/CURRENT_GOAL.md`. Changes comprise unrelated #6616, #4972/#5752, #59, #6256, #6689 and refusal-terminality evidence plus the analysis index.
- S01 remains unrun and unchanged. No same-name S02 branch exists; the planned additive path and `execution/formal-s02/{candidate,auditor}/` are absent on main and in the local package before formal work.

## Host-only construction

- Native Windows AMD64, CPython 3.11.9, standard library only. No WSL container, GPU/CUDA, model, network, GUI, or OS input was used during construction.
- `python -B -m unittest -v`: **5/5 PASS**. `python -B -m py_compile builder.py candidate.py auditor.py test_protocol.py`: PASS.
- The builder, image decoder, candidate, and auditor were exercised only through unit/construction tests and temporary outputs; no formal CLI command or `execution/formal-s02` output was invoked.
- Initial construction exposed two fail-closed attribution defects: the occlusion control was first called shape deformation, then off-axis motion after changing the silhouette quadrants. The frozen image-only rule now first uses quadrant imbalance jointly with silhouette aspect change to identify the half-occlusion; a circular translated target remains off-axis. The auditor independently applies the same observable boundary rule. Both initial failures remain described here; they were corrected before freeze and did not consume a formal allocation.
- The paired non-identifiable cases are byte-identical in both frames and yield identical normalized candidate outputs (`UNKNOWN`, `insufficient_scene_flow`). Six frozen raw corruptions (missing/duplicate row, forged frame hash, forged geometry, false SAFE, fabricated release lead) all fail audit in construction. Auditor reconstruction now compares every emitted center/radius/aspect/anchor/scene-flow metric against the image bytes.

## Local runtime readiness snapshot (read-only)

- `wslc.exe`: `C:\Program Files\WSL\wslc.exe`, WSLc 3.0.1.0; `wsl.exe --version` reports WSL package 3.0.1.0.
- WSLc `list --all --format json` returned 48 exited containers and zero running containers. The output lists were not modified. Existing images include cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (`linux/amd64`, CPython 3.12.15; local image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`). No image pull is planned.
- C: free space snapshot: 18,520,514,560 bytes. RTX 3080 Laptop GPU snapshot: 11 MiB used, 0%; GPU is not required or passed to this CPU experiment.
- Process inspection found an unrelated Django `manage.py runserver` parent/child and two WSLc `events` watchers. No process was stopped or touched. A fresh inventory is mandatory immediately before formal run.
- Several same-goal Codex tasks are active. Their threads were read; none was found running a WSLc container at the snapshot. The exact WSLc inventory, branch, main, image digest and output-collision gates must be repeated immediately before the bounded run.

## Planned formal window and one-shot boundary

- Window (UTC): `2026-10-02T20:50:00Z` to `2026-10-02T21:05:00Z`.
- Candidate maximum 1; auditor maximum 1, only if candidate exits 0; retries 0.
- Candidate and auditor use distinct `--rm` WSLc containers, image by immutable digest, `--pull never`, network `none`, one CPU, requested 512 MiB memory, source mount read-only and separate output mounts. Resource flags are configuration, not evidence of enforcement.
- Before either run, recheck main equals the frozen S02 main, source/fixture/Oracle hashes, PR branch head/path, output absence, cached image identity, WSLc running-container/process inventory and disk headroom. Any failed gate means STOP with no substitute or retry.
- If the one-shot window elapsed before the exact preflight is complete, record a pre-candidate STOP; do not roll the window forward silently.
