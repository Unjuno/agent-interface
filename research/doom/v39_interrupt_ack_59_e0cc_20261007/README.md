# Fatal-cover interrupt acknowledgement repair

An interrupt acknowledgement without completion kept the old fatal-cover path
waiting for the pending planner. The repaired path closes its still-pending
transport before joining the worker, while retaining the original cover error.

See [RESULT.md](RESULT.md) for the measured boundary, controls, and limits.
[MANIFEST.json](MANIFEST.json) binds the passive [evidence archive](evidence.tar.xz).
Final focused tests: 101 normal + 101 optimized; workspace index: 22 tests.
Nine actual inert-peer Popen cells are retained, including the first baseline
rescue. Independent saved-data checks pass 42 original + 26 final predicates.
All original construction and auditor failures remain. No live game, model,
native input, physical-release or worst-case shutdown result is claimed.
