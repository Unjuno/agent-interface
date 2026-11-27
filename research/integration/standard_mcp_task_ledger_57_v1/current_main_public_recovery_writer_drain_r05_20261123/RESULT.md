# R05 A01 result — current-main public recovery writer drain

**Disposition:** `PASS_FOCUSED_FAKE_REGRESSION`.

Frozen source main was `d5a378ecfd0d6fd71804fc509f9d6ecd31be0dd1`. The tested `runtime/cli_v1` and `runtime/core_v1` trees were checked out at that exact commit before adding this evidence packet.

The exact unittest `test_public_compiled_caller_joins_exact_result_query_and_task_oracle` passed 1/1 in normal mode and 1/1 under `-O` on Windows CPython 3.11.9. Elapsed test time was 0.672 s and 0.531 s respectively; both child exit codes were 0. The test asserts the source action remains UNKNOWN and replay-denied, recovery separately confirms release and the late-input horizon, and the independent fixture oracle matches the exact call/operation/target generation. It also waits for the exact atomic report write to finish before temporary-directory teardown.

This is a focused Fake Win32 test only. It supports that the R04 observation-timeout/report-temp cleanup symptom did not reproduce in this single current-source case after the `1bf4d236` test drain change. It does not erase R04's 7/10 mixed result, establish repeated reliability, exercise real OS input or a GUI, or qualify #57 task success, efficiency, MAP01, WSLc, Research Preview, or a distributable runtime.

**Setup deviation:** the first wrapper invocation used the wrong working directory and both Python processes failed before importing the target test. Their exit/byte-count summary and the inspected normal traceback are transcribed in `AMENDMENT_A01.md` and `SETUP_ERROR_TRANSCRIPTION.txt`; the original setup stderr bytes were overwritten before separate archival. Those setup errors are excluded from the R05 target-test cohort, and this custody loss is disclosed.