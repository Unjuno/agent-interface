# Formal allocation STOP report — #4827

- Allocation: `capture-visibility-docker-4365-20260927-01`
- Frozen source/protocol commit: `e9c4fd7acbc628947c830df0e363f559f03410ce`
- Container image ID: `sha256:acf83a1dfafd43c44d81e2f28f85fc844fa43dc73f36b689a862dd924f9235d0`
- Producer container ID: `7716c48e358f58739d50a168f7e13c730058a405fcad0a25b0de4b676ba84e95`
- Producer exit: 2; OOM: false; network: none; read-only root: true; 1 CPU; 1 GiB; 64 PIDs.
- Formal schedule attempted once, in order: CLEAR, SIBLING_HALF, SIBLING_FULL, CHILD_HALF, CHILD_FULL, RESTORED, then the same six for replicate 2.
- Result: 12 sessions attempted; 6 complete, 6 STOP_CASE; 12 native captures; 2 CLEAR and 4 UNKNOWN assessor outputs.
- First STOP: case 3 (`CHILD_HALF`, replicate 1) at `parent.query_tree()` child attribute inspection, `AttributeError('class')`. Same defect stopped cases 4, 5, 9, 10, 11. No captures were attempted in those six sessions. Xvfb exited 0 and each socket/auth file was removed.
- Independent raw auditor ran exactly once in a separate offline Docker container. It verified the 4-source manifest, all 12 available images and their raw digests/geometric composition; it returned `FAIL_RAW_AUDIT` / `STOP_AUDIT` because six scheduled cases lack receipts/captures and the 4/8 assessor and 24-capture gates are unmet.
- Disposition: `STOP_DOCKER_CAPTURE_PREREQUISITE`, not PASS and not a behavioral contradiction. No retry, replacement, pooling, or source change was made under this frozen allocation. A corrected successor allocation is required to test all six conditions.
- Full producer/auditor outputs, complete container inspections, JSON summaries, raw files, and per-session Xvfb logs are retained alongside this report. Raw capture files are 38,400 bytes each; SHA-256 is recorded in `result.json` / `cases.jsonl` and the independent audit.

The fixture bug is that Python-Xlib's `GetWindowAttributes` reply does not expose a `.class` attribute as assumed. The frozen source was not changed after the run; any fix must be versioned and re-frozen in a new allocation.
