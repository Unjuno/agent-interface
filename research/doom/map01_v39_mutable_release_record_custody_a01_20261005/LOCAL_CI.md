# Local verification record

Executed before packaging this result:

- `python3 -B -m py_compile research/doom/map01_v39_mutable_release_record_custody_a01_20261005/*.py` — passed.
- No-input preflight before A02 — `PREFLIGHT_OK_FROZEN_SOURCE_IMAGE_NO_OUTPUT_NO_INPUT`.
- `python3 -B -m unittest -v map01_v39_perkey_bridge_a01.test_bridge` from `research/doom` — 2/2 passed.
- `python3 -B -m unittest -v test_check_workspace_index` and `python3 -B check_workspace_index.py --git-tree` from `research` — 1/1 passed; 159 reachable top-level directories.
- `python3 -B .github/check_public_navigation.py` — 26 documents, 1,804 repository-relative links passed.
- `git diff --check` — passed.
- Independent raw-only A02 audit — 2 cases, 0 mismatches; formal_01/formal_02 audit outputs are byte-identical.
- Package SHA-256 manifest — verified after final edits.

The no-input preflight was intentionally not accepted as a post-run check: when invoked after A02 output existed, its write-once guard refused to proceed. This did not launch a container or candidate. No full-repository test suite or GitHub-hosted CI success is claimed here.
