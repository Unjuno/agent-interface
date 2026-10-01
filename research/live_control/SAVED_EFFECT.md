# Scoped saved-effect evidence candidate

`saved_effect.py` separates a saved first-sheet cell predicate from program
terminal. It returns VERIFIED for a matching sample, CONTRADICTED for a mismatch
at an explicitly closed evaluation boundary, and UNKNOWN for a mismatch while
the observation window is open or evidence is unavailable. Formula cells remain
UNKNOWN because this reader does not calculate them. An action ID is correlation
metadata: every result explicitly says attribution is not established and grants
no authority. VERIFIED applies only to the declared cells in the sampled bytes.

`probe_saved_effect.py` reuses eight frozen route-comparison workbooks: five
successful saved endpoints verify and three unsaved endpoints contradict. Six
additional controls cover missing/corrupt evidence, a still-open window, a formula,
a declared preserved B1 cell changed unexpectedly, and a matching workbook.
The four evidence-insufficient controls return UNKNOWN; collateral change
contradicts; the matching control verifies. Results, available control workbooks,
and listed source/artifact hashes are in `results/saved-effect-01`.

This is DEVELOPMENT_KNOWN artifact replay and candidate code, not a live adapter
integration or held-out benchmark. It does not yet reduce planner boundaries or
measure assistant time to semantic completion. Bytes are read once, hashed and
parsed from that same snapshot, but the read is not an atomic filesystem snapshot
and the artifact may subsequently change. There is no session incarnation,
baseline-delta attribution, writer attribution, or full-workbook preservation
proof. Caller-declared observation closure is trusted; it does not establish
that a delayed application write can never occur. Only the declared first-sheet
cells are checked; undeclared collateral edits are outside this contract.

This implements a bounded part of Issue #34, without claiming its full effect
contract. Next bind this evidence to a live finalization boundary, retain program
terminal independently, and test unavailable/delayed evidence before using it to
drive planner recovery. Do not weaken the existing finalization error handling
or automatically retry an UNKNOWN effect. No default promotion or freeze credit.

Run with a fresh output directory:

```sh
python3 research/live_control/probe_saved_effect.py
```
