# Separate ordinary revision-2 verification

Target head: f0ca86d295265f7ee55da2d4805b5ab471944d3a, PR #6865.
No original reviewer/A18/C01 outputs are regenerated or changed.

H/T/D: Read the sixteen retained reviewer rows through the exact revision-2 pure
checker and require original acceptance plus rejection of all fifteen negatives.
Then, as a separately identified exact-JSON type boundary, test two authored
single-field True-to-integer-1 changes: single teardown appended witness.verified,
and cancellation teardown's matching final snapshot witness.verified. The positive
retains all booleans. Exact receipt/witness equality must reject these type changes;
Python dictionary equality may alias them. Retain every decision and exception.
The independent raw-only projection checker is reused unchanged for truth.

C/U: This is explicit ordinary engineering review, not a new formal allocation or
an extension of the initial fifteen-case frozen census. No backend authenticity,
original raw fabrication, physical release or runtime defect is claimed. Both
counterexamples concern a proposed exact recorded-witness equality condition.
