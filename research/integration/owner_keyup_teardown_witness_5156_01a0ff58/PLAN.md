# Independent teardown witness review

Worker/session: 01a0ff58-2d0b-7eb1-8b33-c8b69e63563a; FINAL-v5.
Target: PR #6865 exact head a424f2c32c5550989cfdbc9a4a4f89e69454fb20.
Parent scientific question: #5156. Review output only; no author file edits.

H: The new supplement checks teardown receipt identity but may accept disagreement
between that receipt and its recorded owner witness, or a verification timestamp
outside the teardown caller interval. Historical positive data are not alleged
incorrect. This is a distinct boundary from the author's ten controls.

T: Before observing outcomes, freeze one unchanged positive and fifteen authored
single-field mutations: for single/two-key appended witnesses, replace owner,
intent, or verification time (six); for each of three teardown receipts, move
verification one ns before caller start or after caller return (six), or change
the verification timestamp one ns while remaining inside the bracket (three).
Run the retained and supplemental pure functions on private copied JSON only.
A separately implemented raw-only checker verifies exact single-leaf deltas,
the census, hashes, and independent receipt/witness consistency conditions.

D: Coverage gap only if a contradictory copied row is accepted with no errors.
Report each gate separately: nested verification time, receipt-to-final-snapshot
join, and appended-witness-to-receipt join. The unchanged original must satisfy
all predicates. Any exception, wrong denominator or hash mismatch is a failed
review check. No statistical success, physical release, or new formal allocation.

C/U: These are authored consistency constraints on the particular retained A18
shape, not backend authenticity. Future lease deadlines are excluded. The cancel
teardown has no appended witness and a legitimate null intent. Exact witness join
uses the recorded owner-release projection excluding caller-only timestamps.
One-ns mutations test exact finite consistency, not clock accuracy or measured
performance. Existing A18/C01 results and sources remain immutable.

Resources: one host Python process; no backend, input, GUI, container, GPU or model.
Output bounded below 1 MiB; fresh private directory; no main or source changes.
N/common deadline unknown; neither is increased or reset. Relevant all-state
teardown/witness searches found #5156, #6625 and #6865, without a matching current
claim. Unpublished work cannot be excluded. This is independent technical review,
not a committee vote or permission to apply a main update.
