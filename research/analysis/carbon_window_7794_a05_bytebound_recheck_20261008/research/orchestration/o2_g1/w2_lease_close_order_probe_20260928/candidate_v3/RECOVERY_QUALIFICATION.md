# Recovery qualification — Issue #5127 candidate v3

**Historical candidate only; superseded for the current lease-authority rule.**
This file qualifies the eight original v3 files restored unchanged from the
closed, unmerged PR #5142 branch. It does not change the frozen v3 result or
promote it above the later v4 finding.

## Provenance and reason for recovery

- Original branch: `research/w2-lease-authority-contract-v3-20260928`, exact
  tip `c62c117bba7f1ed54635c4ccc84d7ceee2d6ba5e`.
- PR #5142 was closed unmerged as superseded by the open-time successor v4.
- Issue #5127 requires preservation of predecessor results, and the merged v4
  report explicitly states that v3 remains unchanged and its tests belong in
  the combined regression suite. The original eight v3 blobs are restored
  byte-for-byte; the separately recorded first enumerator STOP remains in
  `PRELIMINARY_ENUMERATOR_FAILURE_v3a.json`.
- The five frozen contract/schema/fixture/verifier/auditor blob IDs in
  `FREEZE_lease_authority_v3.json` were rechecked after main advanced to
  `30ebf1340ce2fc61b8932e1bdd262dc4bcd2710c`; they remain identical.

## Scope correction and limits

V3's `PASS_FINITE_LEASE_AUTHORITY_POLICY_ONLY` answers only its frozen rule for
LEASE_CLOSE and PROGRAM_TERMINAL. It does not test the LEASE_OPEN lower bound.
Merged v4 demonstrated that v3 can label a pre-open edge authorized; that is
why v3 is retained as historical evidence, not as the current complete policy
or a production/runtime result. No formal/container/live-authority work is
claimed or authorized by this recovery.

## Local verification during recovery

The unchanged v3 candidate/oracle passed all 48,384 combinations with zero
candidate/oracle or stated-rule mismatches. V3 focused tests passed 5/5; the
existing binding suite passed 15/15; the close-order CLI suite passed 6/6; and
the v4 focused suite passed 7/7. The v4 enumerator independently passed
1,161,216 combinations with zero mismatches. This is 33/33 host tests across
those suites plus the two finite enumerations. Runtime was local Python 3.14.5,
not the historical Windows Python 3.12.10; no Docker/OrbStack, model, GUI,
input, or external effect was used.

The original v3 test expects a fixture alias directory that was absent from
current main. A relative symlink now maps that expected path to the canonical
frozen fixture at `../w2_lease_actuation_binding_5101_v1/fixtures/trace-cases.json`;
the target blob ID and SHA-256 match the v3 freeze. The eight original v3 files
remain byte-identical to the source branch. The first local invocation before
the fixture alias and per-directory test paths were set up stopped on
missing-file/import-path errors; those are replay-environment setup failures,
not scientific failures, and the corrected runs above completed successfully.
