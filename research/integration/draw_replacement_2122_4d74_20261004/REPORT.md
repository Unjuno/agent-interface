# B02: actual Draw replacement breaks retained-reference admission

Successor boundary experiment for Issue #2122 and B01 (PR #7331). B01's unchanged created-reference result is preserved. This experiment tests live membership after replacement; it does not repeat or regrade B01.

H: retaining the original Python UNO reference and matching its name, position and size may fail to establish that it is still a member of the live page.

T: one container invocation, four fresh documents in order positive_0, replacement_0, replacement_1, positive_1. Setup creates A at (1000,1000) and B at (2000,1000), size (500,500). A separate UNO process moves A/B to x=1700/2700. In replacement cases it removes A, creates a distinct generation1 A with the same visible fields, and restores page order. The candidate retains the original created A reference, compares its visible fields against current A, then invokes setPosition to x=1900 if admitted. The required replacement behavior is refusal with zero setter calls.

D: first frozen auditor exit 1, FAIL_OR_HOLD. Producer/container exit 0. Both ordinary controls admitted once and saved A at x=1900/B=2700. Both replacements also passed the guard and invoked the old reference once, failing required refusal. Independent observer and saved FODG agreed that replacement A remained x=1700, B=2700, and A's fixture generation was generation1. Auditor errors are admission:replacement_0__fresh_read_reference and admission:replacement_1__fresh_read_reference. No retry or regrade occurred.

C: pinned image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d, WSLc container, CPU 1, memory 512MiB, network none, user 65534:65534, read-only source mount and writable output. No model calls. Root filesystem is not claimed read-only. Raw resource/process data and first logs are retained.

U: do not adopt the B01 guard for replacement or generation safety. The failure motivates an independently qualified membership/generation admission mechanism. Python identity is not a native identity proof. Fixture generation titles belong to the scorer and are not authenticated runtime provenance or guard inputs. This does not establish a particular native pointer/cache branch, atomic CAS, race safety, population failure rate, or model value. Issue #2122 remains open.

Evidence: FREEZE.json covers six pre-run sources. FILES.json in the publication covers copied source, raw results, all four FODG files, writer/observer outputs and first audit logs. Publication README, FILES.json and .gitattributes are outside the manifest. Namespace .gitattributes preserves original bytes. Independent audit is read-only and does not replay the experiment.

GitHub first result: https://github.com/Unjuno/agent-interface/issues/2122#issuecomment-5975029179
