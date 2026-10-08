# Applicable local replay gate

The current configured workflow .github/workflows/map01-3270-replay-gate-repaired.yml was inspected from origin/main 13cd5f3dcdf43bfc2c6153e489753dd9f1077861. Its literal test source research/doom/test_map01_scorer_scheduler_replay_3270.py was copied as test_gate.py without edits and executed once in WSLc.

Command: wslc run --name caller-coupling-local-ci-4d74 --pull never --network none --user 65534:65534 --volume <this absolute folder>:/data:ro sha256:f649ccab8aec3b94e451c6b0037e60fca72d7d7559381f8cd4aa98530b786c55 python3 -B -m unittest -v /data/test_gate.py

First result: two deterministic unittest methods passed, exit 0. first.log and EXIT.txt retain output. No original live or formal producer replay occurred. This is the configured test's local result, not GitHub Actions success or identical environment: hosted CI uses python:3.12-slim and Ubuntu24.04, while this WSLc image includes additional native libraries.

PR creation was rejected again with HTTP403 secondary content-creation limit at server timestamp 2026-10-03 21:20:56 UTC, request C81F:3370E0:C0D6DE:E5F8FD:6AC171B4. The evidence branch remains published; no PR exists and no merge/adoption is claimed. Future creation attempts must be spaced out; no alternate-credential bypass.

An initial workflow-path lookup used a nonexistent filename and returned git exit1 before source discovery. No execution was started from that lookup.
