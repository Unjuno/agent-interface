# A04 packet custody recheck — 2026-10-21

This is an additive, read-only custody check of the frozen A04 packet from PR #8844's exact head `b9f4221cdbee93e4186f19ab659f51dca0bc5cea`. It does not rerun the candidate, auditor, or formal allocation, and does not change the original `HOLD_UNCERTAIN` outcome.

## Outcome and evidence

- Candidate: one invocation, 360 synthetic trials, exit 0. Independent auditor: one invocation, exit 1 before writing a summary. The first mismatch remains `feature_loss-30090-viewstate_oracle`, step 0; image detection preceded the privileged ViewState branch and caused an oracle-arm YIELD. No hypothesis result is accepted.
- The archive SHA-256 is `631b987c8184f2fd75be32fb06f9acee9ae59a504cdd441e3fbdb1508d9e945e` (335,880 bytes), matching the frozen artifact record.
- The 2,198 regular archive members match all 2,198 manifest paths, sizes, and SHA-256 values; there are zero missing, extra, or mismatched members.
- The recorded manifest hash `7c75014da1f1581461381238d6c93178bfbf395391874b49aeb032670cf68a6f` is the SHA-256 of the manifest bytes with LF converted to CRLF. The exact Git blob uses LF under the packet's `*.json text eol=lf` rule and has SHA-256 `b420e91571a31aee9a93663e2a7c2cadefb41b11d95091b7c964b67ebf7a9360`. This is an end-of-line representation difference, not a manifest-content or archive-member mismatch.

## Boundary

The candidate-supplied scorer truth is not accepted as a scientific result because the independent auditor did not complete. This remains local deterministic synthetic-fixture evidence only. It establishes no controller method, game or GUI result, model behavior, task effect, safety, or performance. Preserve A04's raw archive and manifest unchanged. Any future test of the corrected oracle boundary requires a separately reviewed freeze and fresh authorized allocation; consumed A04 must not be rerun.
