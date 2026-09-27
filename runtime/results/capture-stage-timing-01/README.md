# Capture preparation and bridge timing construction

## Decision

Integrate additive local timing metadata; retain compression, guard captures and all input semantics. This construction verifies the new measurement boundaries on real X11 captures. It does not establish a speedup, representative task latency, human tempo, token cost or production transport performance.

Source commit: 42c6ffa23 (full identifier in manifest). No functional edits followed the live run. The fixture used the existing WSL PrivateSession and shared observe_in_session path. No model or input dispatch was involved.

## All attempts retained

1. Temporary-file displayfd readiness timed out; zero captures. Failure note transcribed from terminal, no raw stderr.
2. Pipe displayfd readiness timed out; zero captures. Failure note transcribed from terminal, no raw stderr.
3. Explicit display pathname readiness timed out; zero captures. Retained stderr reports Unix listener creation failure. WSL /tmp/.X11-unix was mounted read-only.
4. Existing PrivateSession connected using its abstract-socket-compatible path. A returned public capture was rejected by the bridge because binding changed during capture. This is not an accepted observation.
5. New static window allocation, ten consistent binding samples before measurement. Five accepted captures; all stage timestamps ordered. Setup readiness is not included in timing. This change to fixture setup does not alter runtime guard semantics. run.py is retained only for attempt 5; earlier inline commands are not archived.

The fifth attempt records bridge start to decoded at 112.481, 64.037, 51.991, 45.499, 45.201 ms. PNG encode spans range 15.309–25.285 ms; file creation/write/close spans 0.225–0.306 ms, without fsync. These enclosing and nested intervals must not be added together. One static known fixture and five serial samples are descriptive only. Cleanup evidence records returned session.close, not a complete descendant-process audit.

Historical stable-anchor pair analysis is included: direct 25 captures, GetImage sum 443.146 ms; persistent 70 captures, sum 2315.524 ms. Those original timestamps do not measure PNG or model costs. Historical analysis references and hashes the original reports; those reports remain in the earlier published pair archive, not duplicated here.

Validation: six artifact tests passed, shared protocol/harness checks passed. See retained check logs and CAPTURE_TIMING.md for exact interval semantics. verify.py checks archive hashes and the fifth attempt's retained timestamp ordering and image identities without extracting or running its fixture.
