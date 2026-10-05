# A02 release metadata audit successor

Successor to merged PR #7828; Issue #7976 tracks this audit. The predecessor package and its original disposition remain unchanged.

## H / T / D / C / U

**H.** The prior raw auditor can accept contradictory release metadata because its checks cover identity and nested physical-up evidence but omit the emitted authority bit, optional outer edge, and release reason.

**T.** Against exact current main 6860b585305e539ec93896f5adcbf658cbbd8592, preserve the source-locked raw Git blob byte-for-byte. Replay the seven-case predecessor suite. Test three additional mutations on copied JSON: add outer emitted grants_input_authority=true; add contradictory outer edge=down; and change emitted reason=cancelled while owner cleanup/terminal remain expired. Compare the old and new auditors in normal and optimized Python. Do not run the candidate or runtime.

**D.** Accept unchanged raw. Reproduce all three predecessor false-accepts. Reject the three additions and all six predecessor negatives in normal and optimized modes.

**C.** One synthetic fake-display trace; mutations operate on temporary copies only. Audit method coverage is limited to the declared controls.

**U.** No live X11, OS input, GUI, application effect, gameplay, useful feedback, recovery, GPU, or Issue #59 completion.

## Result

WSLc Python 3.12.15 container: unchanged raw audit PASS; predecessor gate 7/7; successor gate 10/10; all three predecessor false-accepts reproduced and rejected by the successor in normal and optimized modes; five Python files byte-compiled; container exit 0. Candidate executions and retries were both zero. See RUN.json, MUTATION_RESULT.json, and results/container_a02/WSLC_RUN.log.

The first successor source rejected the unchanged raw because it required a missing outer edge field. That construction failure is retained in FIRST_ATTEMPT_STOP.txt. The first successful construction replay used a main package copy with one extra final LF; its output is excluded. The final run fetched and verified exact source blob 78d7e68c6a5b98fc55829e6bab378c0f06cbb335, SHA-256 7a1a85a1cc07971b2bf6aa5e1d62541305b9fe8b55482fe46506d90b90db8b4f. See SOURCE_MISMATCH_STOP.txt and SOURCE_LOCK.json.

WSLc reported missing swap/cgroup limit capability. The command configured 512 MiB but does not claim verified memory enforcement; WSLc CLI did not expose a pids limit. The source bind mount was read-only, networking disabled, and the container used a 64 MiB tmpfs for writable test copies/output.

## Reproduction

From the package directory, mount the package and predecessor input read-only into a local WSLc Python 3.12.15 image identified in RUN.json. Copy the mounted source into a bounded tmpfs and run:

```sh
python audit_successor_v2.py
python test_mutation_gate_v1.py audit_successor_v1.py
python test_mutation_gate_v2.py audit_successor_v2.py
python baseline_gap_probe.py
python -B -m py_compile audit_successor_v1.py audit_successor_v2.py test_mutation_gate_v1.py test_mutation_gate_v2.py baseline_gap_probe.py
```

All test changes are in-memory or temporary copies; the frozen candidate JSON is never edited.
