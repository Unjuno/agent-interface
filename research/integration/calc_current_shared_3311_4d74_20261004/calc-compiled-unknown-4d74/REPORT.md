# #3311 G04: real Calc compiled unknown-effect yield

Disposition: PASS_SCOPED_UNKNOWN_EFFECT_YIELD; full integrated comparison remains HOLD.

One fresh WSLc container ran unchanged runtime.core_v1.compiled_gui.run and NativeHandleBridge from source main 9823419dc71eb6f7fd745bfe8249cf7f7584a3a9. The image is sha256:f649ccab8aec3b94e451c6b0037e60fca72d7d7559381f8cd4aa98530b786c55. The source manifest and decision gates were written before this fresh construction. No prior allocation was replayed. The caller chose the A1 anchor from the new original PNG with sequence/digest binding.

H: a completed native input and save must not authorize a subsequent task mutation when semantic effect remains unknown. The compiled program declares two potential mutations. Its observation adapter actually captures images but deliberately returns saved_effect=unknown; it implements no semantic detector. Admission resolves the scoped image reference, and execution calls the existing bridge, which performs its four native guard checks. This adapter ticket does not grant authority outside that owned call.

The first native operation completed. A second fresh graph observation followed, and the unchanged graph returned SAFE_YIELD/effect_unavailable with one completed transition. Raw inventory contains one admission, one native program, two graph observations, and no effect-verifier call. The second action was not admitted or executed. The graph retained its pending effect rather than claiming task success. This tests the unavailable-effect integration branch with a real preceding application effect; intentional predicate unavailability is not evidence of a working semantic detector.

After termination, a separate saved-XML reader checked 31 and 37, product 1147, the intended multiplication formula, and exactly six populated cells. That scorer never fed a success verdict to the native controller. Four native guard stages were VALID. Public release receipts were verified empty; external key/button state was neutral after input and at cleanup. Three tracked parents terminated. Full descendant cleanup or graceful application shutdown is not certified. WSLc ps was empty after the run.

Commands executed once: run_once.ps1 -Phase construction; host Python audit_once.py. Native client exit 0; first independent reader exit 0, AUDIT.json errors empty. Actual cgroups: cpu.max 100000 100000, memory.max 536870912, pids.max max. WSLc's swap-limit warning remains in host.stderr.txt. These are not whole-host limits or hard real-time guarantees.

Primary image-grounding token/context usage is UNKNOWN. Additional benchmark client calls were zero. No token reduction, latency ranking, matched model comparison, broad reliability, or roadmap completion is claimed. This closes a construction dependency for the prospective same-model integrated comparison: unknown effect must yield before the next mutation. The remaining positive semantic adapter and compiled multi-transition efficacy must be verified rather than substituting native completion for task success.

Adapter limitation: graph captured_ns is stamped after g.observe returns, rather than copying the actual capture timestamp. Actual native capture timestamps remain in raw images, but this construction cannot qualify the graph's observation-age gate. A future version must bind that gate to the original capture time in a verified common clock domain. Consumed source is retained unchanged. This does not alter the observed unavailable-effect yield.

Open-PR overlap read found #7170 owns a different Calc click-to-text study and #7153 owns compiled-fixture clock repair. This packet does not change either source or rerun their protocols; it adds only the real-Calc unknown-effect integration evidence. Other compiled-custody and release-witness PRs remain independently owned.

GitHub delivery remains pending while content creation is temporarily rate-limited. Local artifacts are not described as published or merged. Original G01–G03, A01 failure, and D01 inconclusive evidence remain unchanged.
