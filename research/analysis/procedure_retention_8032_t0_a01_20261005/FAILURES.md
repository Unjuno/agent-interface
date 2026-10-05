# Preserved development and infrastructure failures

1. **TDD RED — missing scorer (WSLc):** the initial five tests failed at the explicit `protocol is not implemented` assertion. This was the expected RED before implementation.
2. **TDD RED — missing matched-exposure validator (WSLc):** four tests failed at the explicit missing-validator assertion; existing scorer tests remained green. Expected RED before validator implementation.
3. **Test-harness construction error (host Python):** an early RED run invoked not-yet-defined methods directly, producing two AttributeErrors rather than behavioral failures. The test was corrected to assert the method-missing gate; the corrected RED run then failed as expected. No candidate result was claimed for the erroneous run.
4. **Candidate implementation failure (host Python):** power-rationale implementation referenced an undefined `arms` name; the suite reported one NameError. Fixed by using the frozen three-arm count; subsequent normal and optimized suites passed.
5. **Candidate validation gap caught (host Python):** shortening one training-packet list was accepted despite six declared task opportunities. Added candidate and independent checks for packet count and version; regression test now rejects the mutation.
6. **WSLc infrastructure STOP:** a later invocation returned `エラーを特定できません / E_FAIL` before test output; a chained `wslc.exe list` also returned E_FAIL. Final-candidate WSLc test count is 0. No restart/retry was attempted; host CPython was used for the final construction tests. Earlier WSLc RED/GREEN runs are historical and do not qualify the final candidate.
7. **WSLc memory warning on earlier runs:** kernel/cgroup did not support swap-limit capabilities. No memory-enforcement claim is made.
