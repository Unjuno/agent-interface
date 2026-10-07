# Construction log (pre-freeze)

All entries below occurred before any formal candidate or auditor invocation.

1. Test-first RED: the auditor/candidate files were absent and the CLI contract
   tests failed as expected.
2. Candidate implementation: candidate-only CLI tests passed (50 rows, exact
   seven-byte cue and offsets, no overwrite).
3. Auditor implementation: mutation testing found three false accepts:
   boolean depth alias, boolean lineage alias, and semantically equal but
   byte-different baseline/current JSON. Exact types and frozen source bytes
   were then required.
4. Expanded mutation set found the need to reject unknown authority-bearing
   fields and missing fields whose valid value is explicit null. Exact row key
   set was added.
5. Environment STOP: a read-only container lacked `/tmp`, so unittest could
   not create temporary test fixtures. No formal experiment was attempted.
6. Construction GREEN: rerun with source read-only and only `/tmp` writable;
   all three test methods passed, all sixteen corruptions were rejected, valid
   data passed, and overwrite protections passed.

The discovered false accepts and test-only STOP are disclosed for provenance;
they are not formal experiment outcomes. No candidate or auditor formal run
has occurred.
