# Issue #6515 T0 preregistration

Allocation: `PLANNER-BLIND-CREDENTIAL-ENTRY-6515-T0-HOSTCPU-20261003-01`  
Base: `c33380b3b08792a331ee11f7aee05e3d41437e3e`  
Branch: `research/planner-blind-credential-entry-6515-t0-20261003`  
Path: `research/analysis/planner_blind_credential_entry_6515_t0_v1/`

## H / T / D / C / U

**H.** A request-bound secret-entry policy can distinguish safe delivery to the authorized current target from lookalike/wrong-origin, stale-generation, replay, expired-handle, focus-change and unsupported-route cases, while keeping the secret outside planner/ordinary-log outputs and preserving UNKNOWN when independent application-effect evidence is absent. An ordinary planner-visible typing route cannot meet the non-disclosure condition. Whether an existing credential provider already meets the same end-to-end contract remains an empirical question.

**T.** One finite, no-secret policy-table experiment over 15 synthetic contexts × 5 policy profiles (actor-only typing, visual-only typing, the *documented* agent-browser provider contract, request-bound broker, and no-automation/manual fallback), for 75 rows total. The fixed cases cover valid delivery, lookalike wrong origin, post-capture origin swap, stale target generation, expired and replayed handle, redirected focus/replaced field, unavailable protected input, embedded-origin ambiguity, absent independent effect oracle, pre-existing authenticated session, masked-field acknowledgement without server effect, missing user authorization, credential-account scope mismatch, and credential-purpose scope mismatch. Candidate and separately implemented raw-only auditor run once each in separate host processes; retries=0. Construction tests use different inline rows and run before the formal freeze. No credential bytes, handles resolving to real accounts, browser/provider code, network, GUI, app login, user, clipboard or OS input are used.

The provider profile is only a conservative transcription of the public documentation cited in Issue #6515: vault/plugin secret separation, origin checks/rechecks, and visible/stable-field checks where documented. It is not an execution or security audit of agent-browser, its provider plugins, or a password manager. Where expiry, replay, embedded-frame origin, or protected-path semantics are not established by that documentation, the profile must remain UNKNOWN rather than be credited or condemned.

**D.** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs all 75 rows with zero errors; the broker refuses all frozen wrong-origin/stale/replay/expired/wrong-scope/no-protected-path cases and skips already-satisfied authentication; neither broker nor documented provider profile exposes modeled secret bytes to planner/log outputs; all unobservable or unattributable effects remain UNKNOWN/non-success; manual fallback never becomes autonomous authority; and all eight corruption controls are rejected. A complete contradictory modeled row is `FAIL_METHOD`; missing/ambiguous oracle semantics are `HOLD`/`UNKNOWN`, not PASS. No H/T1 verdict is available from this method-only allocation.

**C.** All inputs are hand-authored logical flags and the route implementations are finite policy models. The documented provider profile is not the provider executable; manual action is not a human study. Boolean leakage fields are policy assertions, not dynamic information-flow instrumentation.

**U.** This cannot establish absence of byte, timing, length, process-memory, browser, OS, plugin or covert-channel leakage; real origin authenticity; actual fill behavior; side-channel bounds; authentication reliability; user accessibility; or product benefit. It does not establish whether the agent-browser profile or any OS/browser password manager passes a real end-to-end test. A synthetic method PASS is not a confidentiality/security guarantee and does not authorize T1.

## Frozen commands and runtime

Construction: `(cd research/analysis/planner_blind_credential_entry_6515_t0_v1 && python3 -B -m unittest -v test_t0)` before freeze.  
Candidate (one formal invocation): `python3 -B candidate.py fixture.json results/formal_01/candidate_raw.json`.  
Auditor (one formal invocation, only after candidate exit 0): `python3 -B audit.py fixture.json results/formal_01/candidate_raw.json results/formal_01/audit_result.json`.

Runtime is host CPython 3.12 stdlib only. WSLc is not used because current #5085 explicitly prohibits further WSLc calls while the shared bridge anomaly is unreconciled; Docker/OrbStack is not used because the shared container allocation is unassigned. This is a bounded non-container CPU method test with no GPU/model/GUI and no shared runtime activity. No memory-isolation claim.

Formal output paths must be absent at freeze. If source/base/branch, fixture hashes, output absence, ownership, or exact command differs before launch, STOP before candidate. Preserve the first raw result and never retry this allocation.
