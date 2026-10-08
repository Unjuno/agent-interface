# Raw identity correction v2

Before running this audit revision, preserve the original 116 package files,
source/runtime fixtures, frozen cases, raw outputs and every first exit/receipt.
This is an ordinary evidence-gate repair prompted by review 5398441445 and
inline comments 4171212319 / 4171212332. No producer, candidate, mutant,
formal allocation, native backend, input, GUI, model, container or GPU is run.

The original v1 oracle uses Python equality for terminal counts/effect sequence
and does not compare actual execute.expected_sequence with the frozen input.
Four directed single-row substitutions therefore escape its gate. Retain that
original source and reproduce the four copied-data escapes separately.

The new raw-only gate imports only the retained raw-only v1 oracle. It adds
type-sensitive JSON identity; a literal ordered trace and journal reference;
the execute payload's exact type/value binding to independently defined input;
and admission/observation/effect/terminal linkage. Baseline semantic deviations
remain classified by v1. An observed malformed baseline dispatch still binds to
its actual frozen typed input rather than being relabeled as an evidence error.
Exception messages are required nonempty strings, but their exact wording is
outside this identity contract. No new physical effect or clock claim follows.

Checks fixed before outcomes: re-audit the two existing 3,072-row raw files once;
require zero identity errors for each, unchanged baseline mismatch count 2,164,
and combined zero mismatches. Run 16 directed copied-row controls; require the
first four to pass v1 and all 16 to be rejected by v2 with one changed-row
identity failure. Preserve original/changed row witnesses, unchanged-other-row
hashes, full-copy hashes and actual UTC/exit/output receipts. Freeze source and
original input hashes before these operations. Control wall-clock bound is
120 seconds, public controls-result output bound 256 KiB, one CPU thread.

Expected execution commands are audit_v2/auditor.py for baseline and combined,
then audit_v2/controls.py. Do not repeat any initial failure to obtain success;
record and version any wrapper repair independently. Runtime unit results are
reused only as original scoped results; this revision changes no runtime source.
Updated head/content digest and explicit committee votes are required before
application. The v1 correction objection is retained, not erased by other votes.
