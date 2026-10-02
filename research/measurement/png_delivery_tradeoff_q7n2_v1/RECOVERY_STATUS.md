# Recovery status (2026-10-01)

This additive directory preserves the exact nine-file source/plan/environment
freeze from original branch head `662e914f9abf02db877c17524cec49139bda9182`.
The FREEZE manifest declares 16 source/corpus entries, but the branch contains
only the nine readable source/gate files; the six pixel/capture payloads and
formal row evidence are absent. Do not recreate these bytes from descriptions
or reported metrics.

The Issue reports 36 completed deliveries and
`HOLD_NO_DELIVERY_RANKING_DISCRIMINATOR`; those are historical reported
outcomes, not independently re-audited here. The original raw-only audit,
controls and complete corpus package have not been recovered or rerun.

Validation during recovery:

- All nine original branch file Git identities matched byte-for-byte.
- In a read-only, network-disabled Python 3.13.5 container, all 6 Python files
  syntax-compiled.
- The frozen study test could not import because Pillow is absent from the
  available container (`ModuleNotFoundError: PIL`). No dependencies were
  installed; this is an environment STOP, not a test PASS or scientific FAIL.
- No formal delivery or GUI experiment was rerun.

This is source preservation only. Issue #4401 remains open; the missing exact
corpus, formal raw records, audit and controls remain a delivery HOLD.
