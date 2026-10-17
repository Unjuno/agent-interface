# Construction and pre-freeze checks

- Intake: Issue #1998 was open; main/base was `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`; A02 PR #8770 and A03 PR #8779 remain separate/open; A03 is permanently retained as `HOLD_RUNNER_EXIT_UNCAPTURED` and is not rerun.
- A04 distinction: main `ImageArtifactSink`, Pillow 12.3.0, and 21 exact archived GUI PNG frames from the four `baseline-screen-02` observation ledgers. A02's synthetic gray8 and A03's synthetic stdlib PNG inputs are not reused as A04 result rows.
- `build_design.py` enumerated 4 observation ledgers and 21 unique pixel frames and emitted 441 preregistered cases (420 crop size/placement combinations and 21 full-bounds controls).
- Pre-freeze Python: Codex bundled Python 3.12.14 with Pillow 12.3.0. `python -m unittest discover -s . -p 'test_*.py'`: 6/6 PASS; optimized `python -O -m unittest discover -s . -p 'test_*.py'`: 6/6 PASS.
- Construction suite includes exact pixel-digest checks for all 21 archived frames, output decoding with the independent standard-library PNG decoder, PNG CRC mutation rejection, canonical metadata/base64 byte counting, exact production encoder import/version, and a subprocess exit-code custody test (child exit 7 recorded exactly).
- Container preflight: read-only `docker context show` returned `orbstack`; `docker image ls --digests` failed before listing images with containerd blob `operation not supported`. No container was started.
- Sandbox construction: `/usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' <Codex bundled Python> -c 'print(...)'` launched successfully. This was only a profile/runtime smoke check, not a candidate/auditor invocation.
- Candidate formal invocations: 0. Auditor formal invocations: 0. Retries: 0. No formal result is claimed at construction time.
