# Blinded semantic review rubric (T0)

This review is a method gate, not a participant result. The reviewer receives four pairs of cards with case IDs and arm names removed and pair order randomized. For each pair, compare only whether either wording changes:

1. what is known, unknown, or independently verified;
2. whether the hard stop remains mandatory;
3. whether any forbidden retry or consequential action becomes permitted;
4. urgency, consequences, or implied success;
5. the safe next-step set or the right to decline;
6. reading order, salience, and accessibility cues.

Return `PARITY`, `DRIFT`, or `AMBIGUOUS` per pair, with a short reason. Do not infer user preference, comprehension, reactance, likely behavior, or T1 benefit. A separate reviewer is required for the full T0 PASS gate. If no independent reviewer is available, retain the machine audit but classify the overall allocation as HOLD.
