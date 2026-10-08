# Receipt-pointer evidence rescue #6893

All 26 original package files from abandoned remote tip
`848b5bcce3e23ea306665761857ae6a1effc8fbe` are preserved without changes.
Production repair already arrived via #6874; current main adds further strict
typed marker validation. Neither production code nor the old regression import
is replaced by this archive. The independent Windows review is historical,
not a vote or current-main integration certificate.

H: retained finite pointer records reconcile to their exact frozen sources.
T: verify 24 manifest hashes, both complete saved 3333-row audit receipts/five
corruption controls, baseline source witness and 24 zipped diagnostic hashes.
D: unchanged baseline, original source history, raw, freeze and lossless logs.
C: read-only archival checks; no original producer, zipapp, native backend,
input or formal allocation is re-executed.
U: retained engineering evidence only; no current runtime, arbitrary JSON,
GUI, safety, latency or task-effect qualification.

Run `python -m unittest discover -s runtime/results/receipt_pointer_rescue_6893 -v`.
The archive-smoke receipt's binary zipapp is not in the retained package: its
historical source/hash/9-check receipt is preserved, but smoke is not rerun or
claimed independently verified. Original red tests and dependency-missing
attempt remain failures; the later passing checks do not overwrite them.
