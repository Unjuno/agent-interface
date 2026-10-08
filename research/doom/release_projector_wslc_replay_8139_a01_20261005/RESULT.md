# WSLc verification of PR #8139 producer-bound projector

Date: 2026-10-05 (Asia/Tokyo)

## Frozen scope

- PR #8139 head `9648fc1dc6f68fa6702afb4d59b3c6cc8377a9e9`; PR-reported base/main `19a6b723e58ccfd2b8265e88659589ef9223fcc9`.
- Eleven source/test files were selected from the PR's `green-v1/sources.json` closure. Their SHA-256 values are in `SOURCES.json`; all match the PR manifest.
- The same eleven closure paths were unchanged between the PR's tested base `1703ec621dbe12a8be5fc808e9e3d1f77b775829` and current main `19a6b723e58ccfd2b8265e88659589ef9223fcc9` at freeze time.
- Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (locally present Python 3.12 image).

## Execution and result

One WSLc invocation, network disabled, 1 CPU, `--pull never`, read-only source mount, no GPU, no retry:

`wslc run --rm --network none --cpus 1 --pull never -e PYTHONDONTWRITEBYTECODE=1 -v <frozen-closure>:/audit:ro -w /audit/research/doom python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 sh -c 'python -m unittest -v test_project_v39_release_measurement_v1 test_project_v39_release_measurement_composition && python independent_probe.py'`

Exit 0; all 16 projector/composition methods passed in 0.360 s. The producer composition suite used synthetic Xlib and exercised actual V12 owner-thread, V3/V4 wrapper and batch publisher code; it did not run Session, typed executor/lowering, the full V39 loop, or a game.

Independent single-field controls: untouched fixture → ready / 1 row; attempt ordinal `1 -> true`, release identity step `2 -> true`, and release batch step `2 -> true` each → not ready / 0 rows. Exact emitted output is `formal.stdout`, SHA-256 `1D001F66C9F20C15052127B9066B039DC11FDEE205ABC6D9C047BB8F402CFBCE` (41,751 bytes). The independent probe source SHA-256 is `88EF00EA024A02F2A61AA9F9B291167D7DD1C0E3724A2AE8D164D906B6F8CC92`; PRE-RUN SHA-256 is `1DD4220E672857DD50C28A38D9EA39FB607423DE6969CE092A460F844256FDC4`.

Disposition: `PASS_SCOPED_WSLc_REPLAY` for the source-bound projector contract.

## Limits

This verifies synthetic measurement projection only. It does not establish physical key state, application consumption, real X11/game behavior, model-latency response, useful feedback, bounded recovery, or MAP01 success. PR #8139 remains draft and needs its own current-main integration, content review, and merge gates; this replay does not grant any live allocation or make a quorum decision.
