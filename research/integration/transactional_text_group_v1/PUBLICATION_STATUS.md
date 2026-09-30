# Recovery status — reported result, incomplete raw capsule

The original `transactional-text-group-16-formal01` allocation is consumed.
This publication preserves its frozen plan, report, failure history, pack
metadata, and the three raw parts currently present on the old branch. It does
not rerun or independently validate the formal GUI experiment.

- `REPORT.md` records 45 GUI sessions and a scoped compensation-boundary
  outcome, including three audited `FAIL_WRONG_COMPENSATION_COLLATERAL` cases
  for blind compensation. Treat those counts and audit claims as the original
  report, not as independently re-audited evidence in this recovery.
- `PACK.json` declares six parts and a 50,220-byte archive. Only parts 00–02
  are available here. Their individual encoded/decoded sizes and SHA-256
  values match the manifest; the decoded 25,110-byte prefix cannot be
  decompressed as a complete archive. Parts 03–05 and the remaining raw audit
  members are unavailable in this branch snapshot.
- `UNPACK_CHECK.json` retains the historical `PASS_LOSSLESS_UNPACK` claim, but
  the currently available three-part package cannot reproduce that check.
- No source capsule was restored from the incomplete raw archive, no formal
  command was run, and no raw-only audit or corruption controls were rerun.

Disposition: `HOLD_PUBLICATION_INCOMPLETE`. Preserve the reported historical
outcome and known comparator failures without promoting this partial readback
to a verified scientific PASS. This old live-GUI allocation is distinct from
the later exploratory saga probes recorded on Issue #16; do not pool them.
