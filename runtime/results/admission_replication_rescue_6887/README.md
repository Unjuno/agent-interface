# Admission-context replication rescue — PR #6887

Source: `ddc2822aaa98c91e99792f2cf08a610deed83aee`.
The 27 files in sibling `admission-context-01a0ff2d` are retained without edits.
The production repair already arrived through #6866/#7066; no runtime source
is replaced by this archive. The original proposal and votes are historical,
not approvals of this recovery delivery.

H: retained records still reconcile to their frozen source witnesses.
T: re-audit the saved 44-row baseline/fixed records, nine corruption controls,
and both public manifests with their documented source aliases.
D: byte-preserved public records, source witnesses and publication receipts.
C: raw-only checks; no producer/native/backend/formal allocation repeated.
U: no physical currentness, release, task benefit or product qualification.

Run `python -m unittest discover -s runtime/results/admission_replication_rescue_6887 -v`.
This audit does not recreate the private unredacted baseline log: the existing
LOG_PUBLICATION receipt explicitly identifies that redaction. It does not
recover #6866's separately disclosed missing logs. Historical failures, skips,
and external_non_author_review=false remain unchanged.
