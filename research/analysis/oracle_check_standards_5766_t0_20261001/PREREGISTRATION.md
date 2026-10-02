# #5766 T0 pre-registration — bracketed semantic check standard

**H:** On a finite frozen task-oracle deck, bracketing the candidate interval with the same positive/negative/UNKNOWN check deck catches a changed artifact meaning even when scorer bytes are unchanged; a meaning-preserving scorer/app schema version change is not falsely treated as drift; events outside deck coverage are UNKNOWN rather than PASS.

**T0:** CPU-only, no model/GUI/live app/input. Freeze five cases (valid positive, wrong target, collateral effect, unsaved state, UNKNOWN), independent expected semantics, candidate events (one covered, one out-of-coverage), and three app/scorer profiles. Run once in the pinned Python container: nominal v1; app semantic drift with unchanged scorer code bytes; equivalent app/schema+scorer version change; and out-of-deck candidate event. Candidate retains full pre/post row outputs. An independently written auditor directly enumerates expected labels and disposition; four raw mutations: missing postcheck, swapped frozen label, UNKNOWN→PASS, and post-candidate reference backfill.

**D:** `PASS_METHOD_SCOPED` only if in-deck drift changes at least one well-formed score under the same scorer hash and is held; equivalent versioned controls remain eligible for further task audit; out-of-coverage event is `UNKNOWN_COVERAGE`; all rows retained; auditor rejects all four mutations. This does not prove a real app scorer drift occurred.

**C:** Constructed deterministic fixture and declared mapping; app profiles and oracle labels are stipulated. No randomization, user, model or live environment.

**U:** Five check rows do not certify unseen semantics or real oracle independence. Synthetic result cannot close #12, #57, #59 or production/effect validity. T1 needs replayable raw outcomes, independently adjudicated task semantics and separate authorization.

No candidate/auditor execution until FREEZE.json, exact image digest, branch/path and hashes are committed and read back from GitHub.
