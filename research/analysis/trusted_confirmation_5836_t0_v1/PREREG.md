# Issue #5836 T0: trusted-path confirmation semantics

**H:** Against the frozen page/tool/agent-content adversary, a separate confirmation channel with an exact request-bound, single-use receipt rejects forged text, stale receipt, target swap, principal mismatch, revocation, replay, and lost-response retry while preserving one matching approval, explicit denial, and safety release. This is a semantic boundary test only.

**T:** Deterministic finite broker/executor fixture; 13 ordered request opportunities, three policies, 39 policy/request rows. Compare `SCREEN_TEXT`, `BOUND_REPLAYABLE`, and `TRUSTED_SINGLE_USE` on identical inputs. A separate stdlib-only raw auditor recomputes every row and applies six in-memory corruption controls. No GUI, UAC, Android, credentials, network, model, human participant, real payment, or privileged effect.

**D:** `PASS_METHOD_SCOPED` only if all 39 rows match the independent oracle; trusted single-use authorizes no `truth=DENY` case; matched approval works once; explicit denial has zero attempts; safety release is not gated; lost response is `UNKNOWN` with receipt consumed and retry denied; weaker controls expose the planned text-forgery, target-swap, and replay failures; six mutations reject. Any false authorization or blocked release is FAIL. Mismatch or incomplete rows is STOP/FAIL_AUDIT.

**C:** An immutable effect plus a request digest could avoid single-use machinery; a simple out-of-band broker prompt may be enough. Existing capability attenuation does not prove channel provenance. Synthetic receipt flags do not prove a real trusted channel.

**U:** This cannot establish OS/hardware trusted display or input, human comprehension, coercion resistance, accessibility, consent quality, or safe product behavior. A receipt authorizes one scoped attempt, not success. T1 is considered only if this test is informative and would use a disposable instrumented UI with no real payments, credentials, or privilege elevation.

The fixture's receipt channel is an independent, non-agent-writable oracle by construction. The adversary controls page/tool text and the post-display request but cannot mint or alter trusted receipts. The safety release action is deliberately outside the consequential approval gate.
