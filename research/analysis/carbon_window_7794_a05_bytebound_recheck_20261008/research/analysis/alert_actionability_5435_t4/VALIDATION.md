# T4 validation record

- Preregistration was posted before the formal candidate invocation: Issue #5435 comment `5911613008`.
- Host and network-disabled container syntax/single-stream smoke: PASS.
- Formal network-disabled container candidate: exactly one invocation; exit 0; 24 streams/120 policy traces retained.
- Independent network-disabled replay audit: PASS; all event rows, five policy outputs per stream, deadlines, counters, and the preregistered model gate recomputed.
- Corruption controls: v1 initially rejected 3/4 because the score mutation rewrote a calibration-like score to the same value. The unchanged failure output is `raw/corruption_controls_v1.json`. The control script alone was corrected; v2 rejected 4/4. Formal candidate and auditor were not rerun or edited.
- `python3 research/analysis/check_index.py --write`, then read-only check: PASS, 215 result/failure directories indexed.
- `python3 research/check_workspace_index.py`: PASS, 146 top-level research directories reachable.
- `python3 .github/check_public_navigation.py`: PASS, 26 documents and 924 repository-relative links (after staging the new evidence path).
- Python syntax, single-stream smoke, and `git diff --cached --check`: PASS.
