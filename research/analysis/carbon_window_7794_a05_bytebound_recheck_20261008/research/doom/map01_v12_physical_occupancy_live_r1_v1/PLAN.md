# MAP01 v12 physical occupancy R1

Issue #1928. Reserved from main `e87f066a6015640dc9c802aeef7d981c40e3eb6a`.

This rung transfers already-retained v12 physical DOWN/UP measurement into the unchanged current MAP01 v13/v3 release-batch semantics. It changes the measurement implementation only: no model, controller policy, plan, task reward, recovery policy or input-authority rule is changed.

Pre-live gates:
- exact current v13/v3/owner-v3/fixture Git blobs;
- exact retained InputOwner-v12 and adapter SHA-256;
- static compatibility ABI PASS;
- retained R0 plan/step-lineage contract snapshot;
- 5.000 ms per-actuation combined edge-censor-width gate, fixed before live execution from the retained #1276 maximum 0.629138 ms with a broad transfer margin.

Execution budget:
1. one excluded construction session only after an exact-head construction lease;
2. if construction PASS, mandatory exact-head/#1928/#60 reread and a separate formal lease;
3. formal exactly one invocation of three fresh sessions; no rerun/replacement/tuning.

Formal session program: one `hold(['a','d'],250ms)` then `observe`, fixed MAP01 threat-contact fixture, no model/provider/network/user desktop.

Decisions and H/T/D/C/U are frozen on #1928. Any live STOP/FAIL is retained before a successor changes source.
