# Planner start admission custody

The adapter reserves admission under its state lock before calling thread/start or turn/start. A second start or session reset is refused while that RPC is pending. Once a valid ID is recorded, the reservation becomes a tracked thread/turn. A thrown response or missing ID leaves the reservation sticky because remote effect is unknown. Reusing the same adapter must not blindly retry or reset. Reconciliation or disposal of the uncertain work is external; constructing another adapter does not prove the old work stopped.

RPC calls occur outside the held state lock. Lock acquisition, transport, cleanup and whole-call duration are not bounded by this change. Cancellation semantics remain: invalidated observations are never eligible answers. Successful completed turns can still precede another turn or a new session. Borrowed grounding clients retain ownership.

Own E29 eight planner boundary regressions and I30 four actual grounding caller regressions use fake RPC only; normal and optimized interpreter results are retained. Standard modules preserve all fixture/helper method ASTs while removing the private command-line/raw-output requirement. Existing ten planner regressions remain applicable under exact unchanged source methods. No provider, GUI, physical release, natural failure rate or performance claim. Grounding model.calls counts completed waits, not all start attempts; unknown sends require a separate ledger. Missing usage remains unknown.

Original baseline, first fixture/audit failures and repair evidence: https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5974231980 and https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5974327311 (part2 5974327500). These data do not authorize actor replay. Prior fixed7283 review and suspended approval do not transfer to this successor.

## Result finalization

Wire completion is not the local result boundary. Admission stays closed through usage retrieval and schema validation. The final result captures the active handle and current cancellation flag under the state lock before making terminal status visible. A cancellation arriving while local finalization is pending invalidates the answer even if the remote turn completed. Interrupt may then reach an already completed remote turn; existing error capture keeps semantic invalidation local. Usage/validation exceptions before result commit keep the old active fence rather than granting retry.

E32 retained five directed fake-RPC/Event cases: before the repair, next schema could make an invalid old answer eligible or reject a valid one, reset could replace the session and late invalidation was missed. Private repaired five normal/O and unchanged selected22 normal/O passed. This generic adapter schema-switch witness does not claim PersistentGroundingModel switches its per-session contract. No real provider/GUI/whole-time/physical-effect/performance claim. Earlier fixed7303 evidence and author adoption HOLD remain historical; this revised source requires fresh fixed-content review.

## Contract and interrupt response custody

The admitted nested schema is copied before RPC; the transport receives a separate copy, so sequential caller or transport mutation does not change local result validation. A late interrupt response is stored only if its handle remains active. This preserves newer turn response/error bookkeeping while the old request still returns its own outcome to its caller.

Schema detachment contributed by 34fb; interrupt response guard contributed by 45e9. Private combined source fa8ac8074cb2e2249cc50682d9d00fbf293e2370bff821122bcd6507bf202e84 was qualified by author I34 own7 normal/O and selected27 normal/O. Prior await_turn finalization remains unchanged. New standard custody test covers caller required/nested mutations, transport mutation, valid control, serial interruption, and delayed success/error responses.

Plain nested dictionaries and bounded fake clients only: copying does not establish consistency under concurrent caller mutation or custom deepcopy behavior. Unknown admission still needs external reconciliation; physical task/input/provider effects, whole-call deadline and performance are unqualified.
