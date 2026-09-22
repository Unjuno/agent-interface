# Retained edit-context dispatch-placement evidence (#4091)

This directory publishes an already completed local allocation. It is **not** a GitHub preregistration, and no consumed GUI/formal case is rerun for this delivery.

Scientific result: `PASS_DISPATCH_PLACEMENT_BOUNDARY_SCOPED`. `HOST_ONLY` produced 8 incorrect edits / 12 cases, `EVENT_EARLY` 4 / 12, and `PRE_CLASS` 0 / 12; PRE_CLASS refused 8 unresolved insertions and completed only the 4 unchanged/unrelated positives. Refusal blocks the application insertion, not native key emission.

The complete original 402-file evidence tree is stored losslessly in the `evidence.part*.bin` archive parts. `REPORT.md`, `AUDIT.json` and `FREEZE.json` are directly readable. Historical `PUBLICATION_STATUS.json` inside the retained tree remains unchanged and truthfully records that the earlier session lacked GitHub writes.

Read-only restore: `python -B unpack_evidence.py /tmp/text-dispatch-4091`. Then run the retained `verify_retention.py`, raw-only auditor, and unit tests from the restored study directory. Do **not** rerun consumed formal IDs.

This is research evidence only: no shared runtime/default, product claim, model benefit, arbitrary GUI atomicity, or roadmap completion.
