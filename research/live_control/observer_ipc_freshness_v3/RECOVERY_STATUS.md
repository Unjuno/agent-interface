# Recovery status (2026-10-01)

This additive delivery preserves the original r3 source/gate/report tree. The
eight source identities declared in `FREEZE.json` match exactly; all six
Python files syntax-compile under Python 3.13.5.

`FIRST_OUTCOME.json` records 40 cases and
`HOLD_FROZEN_AUDITOR_CONTROL_GAP`: one of 11 frozen corruption controls,
`boolean_block`, was ineffective. This HOLD is preserved as reported; the
40-case rows and post-hoc audit are not upgraded or reconstructed here.

`ARCHIVE.json` declares four `EVIDENCE.tar.xz.b64.part*` files, but none is in
the original branch tree. In a read-only, network-disabled Python 3.13.5
container, `unpack.py` stops on missing `part01` before archive validation or
extraction. The formal raw bytes, audit inputs, and corruption-control records
therefore remain unavailable for independent verification. No experiment or
audit was rerun, and no missing bytes were fabricated.

This is source/report preservation only. The r3 outcome remains
`HOLD_FROZEN_AUDITOR_CONTROL_GAP`; it is separate from r2's timeout STOP. Issue
#3944 stays open pending exact archive-fragment recovery.
