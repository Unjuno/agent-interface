# Successor A02 — hard emergency override probe

This additive successor addresses one qualification of A01: A01 validated a declared override field and its corruption, but did not execute the override policy for every dwell-blocked state. A01 sources and raw outputs remain unchanged.

H: An emergency request for the alternate mode must change the abstract selected mode on the same tick, for either current mode and every remaining dwell age; the normal dwell guard must not suppress it.

T: Exhaustively enumerate current mode A/B and elapsed dwell ticks 0..9 (the complete blocked portion of a ten-tick dwell). For each cell, request the alternate mode and independently assert immediate selection, `delay_ticks=0`, and explicit bypass of the regular guard. Mutation controls force the regular guard to be applied, hold the current mode, or report a one-tick delay.

D: PASS_METHOD_SCOPED only if 20/20 cells independently reconstruct as immediate and all three mutations are rejected. Any delayed/blocked override is FAIL; missing cells or disagreement is HOLD. This validates only the abstract policy function, not any real controller or safety authority.

C/U: Finite exact enumeration, two modes, dwell ten. No runtime, hardware, safety owner semantics, GUI, or physical-system behavior is tested.

Formal commands are to be frozen and executed once each: `python3 candidate.py`, then `python3 audit.py`.
