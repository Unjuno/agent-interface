# Issue #59 A07 custody audit — 2026-10-19 r01

Captured 2026-10-19 11:23 UTC from the exact open PR #8702 head, merged preservation PR #9148, and current `main` at `5785f8a991a7e5b86f632e9d2901d73aa409c53e`. This is a read-only source/custody comparison. No A07 allocation directory, live application, VM, or input was opened or changed.

## Disposition

Keep Issue [#59](https://github.com/Unjuno/agent-interface/issues/59) open. Keep PR [#8702](https://github.com/Unjuno/agent-interface/pull/8702) open as a draft with disposition `evidence-custody-hold`. The independent audit package and its reported result are useful and internally checksummed, but the private raw bundle required to reproduce the 2,358-entry manifest and event-stream checks is not present in the inspected tracked sources. Do not rerun the A07 allocation, close either item, or upgrade its HOLD/STOP result.

## Exact source identities

| Source | State and identity | Relevance |
|---|---|---|
| Issue #59 | OPEN; latest update 2026-10-19 04:24 UTC | MAP01 live-control priority and unresolved task-effect question |
| PR #8702 | OPEN draft; head `d2c9fdec7c2d8f4916af68e35dd1350efffe2564`; base `74fc81e0a447ad05e4a2220b16d7949979635fb9`; author `Unjuno` | Independent A07 raw-custody auditor; body says the raw directory is not copied into the PR |
| PR #9148 | MERGED 2026-10-19 04:03:53 UTC; merge commit `38845fc83b698f26051477280eb14937b1907315`; head `86fc8621b6049d503315f109db458f3c3c650ea7` | Preserved the tracked A03–A07 audit and owner-release reconciliation packet |
| Current main | `5785f8a991a7e5b86f632e9d2901d73aa409c53e` | Contains the PR #9148 tracked packet and custody records |

PR #8702's only reported checks are `replay-gate: SUCCESS` and `formal: SKIPPED`; it is still a draft and has no review decision. The report does not treat those workflow results as independent reproduction of its raw-data claim.

## Available path, size, and hash evidence

The PR #8702 `SHA256SUMS.txt` covers its four tracked payload files. I recomputed each SHA-256 from the exact PR-head Git blobs; all four match:

| PR #8702 tracked file | Bytes | SHA-256 |
|---|---:|---|
| `audit_raw.py` | 18,655 | `79d17519c10ff3640bcb394e8b8bdb1571dcbea9bb50eb078301e9bb097f9e8c` |
| `README.md` | 3,629 | `e16f6c145734e2f43260045691cb354255757694b3863d9c2c99e7068cb4abe6` |
| `COMMANDS.txt` | 918 | `a23e633efc8510b9950e8dc9e17efecf08da68d52d8c5b245871b16b0e12f2a6` |
| `RESULT.json` | 8,950 | `2006bda313aab870c2fd25a28e03f34dad35d877680d11613c103a3168c38f65` |

The tracked A07 directory on main contains 21 files. Selected source/result SHA-256 values are:

| Main tracked A07 file | Bytes | SHA-256 |
|---|---:|---|
| `A07_SAVED_TRACE_AUDIT_V3.json` | 6,363 | `a3794ddda5451b7cbade87a8192dbe9319191459e8e7a0182aa63be0a695a509` |
| `A07_SAVED_TRACE_OWNER_RELEASE_RECONCILIATION.json` | 8,619 | `5622800128a3555618a339dc4ab4dac609833f0c476ab8d092c338e23a51b7fd` |
| `SHA256SUMS_AUDIT_V3.txt` | 447 | `44bb4b5fdef3bd8f23e8a4f5544e217fba5ba534153477d780e03f5e7f5de937` |
| `RESULT.md` | 1,514 | `e9b8b6d8f028905f880eeee67fa52c383c2aa420b6996cc60dedb7e7810ec020` |
| `AUDIT_V3_CORRECTION.md` | 3,250 | `983baaea7332fd5f4eea4c8cd7d0d9f3bd10623ac4332085bb97c431657fbe90` |
| `audit_a07_owner_release_reconciliation.py` | 7,861 | `96d48a0e46e2a0612707272f2578f02b1aeeba01e09cbd45a0dd1bb4da2d1d36` |

There is one exact cross-reference: PR #8702 `RESULT.json` reports raw manifest SHA-256 `a7ed0abe21ad1571131511abfb1b248a61ed5d13e7eaafd196caf2a741ef5844`, and the tracked A07 V3 report records the same value. This links the attestations to the same manifest identity; it does not provide the manifest contents or let this audit recompute its 2,358 file hashes. PR #8702 additionally reports event-stream SHA-256 `7b462e6c13277901adeef2ea69234a5e9f3ee0fead69c6dc6846397538404c6e` and freeze SHA-256 `ca09b5063cea529badf8e8f6731a17dd2eb0d4880be3c7a9466294db41a0e1d3`; these values are not present in the tracked A07 directory.

## What the tracked evidence supports

PR #8702's result reports `PASS_RAW_CUSTODY_RECONCILIATION`, with its overall research gate still `HOLD`: 10 matched cancellations, six with admitted input and four before input admission, 30 held-key events, 25 explicit per-key transitions, five cleanup key-up receipts, and ten empty terminal releases. It reports zero hard-health guard exposures, zero positive useful scorer events, zero physically authoritative release transitions, and an alive-but-unfinished run with no MAP01 exit. These are claims in the checksummed result package; without the raw directory, this read-only review cannot reproduce the private-input checks.

The PR #9148 packet independently records `PASS_CUSTODY_RECONCILED_SCOPED` with `formal_pass=false` and the same 10/6/4 cancellation split. Its per-cancellation table maps each of the five missing explicit transitions to one verified terminal owner-release key-up. The receipts are X11 server-side `query_keymap` results after the cleanup attempt; this supports the server-side cleanup classification for those records. It does not establish physical keyboard state or game consumption. The saved-trace V3 result remains `FAIL`, and `RESULT.md` retains the overall A07 disposition `HOLD`.

## Missing artifacts and exit condition

The tracked A07 packet does not contain `SHA256SUMS.json`, `events.jsonl`, `controller_report.json`, `scorer_summary.json`, or `terminal_score.json`, nor the private 2,358-file raw set. PR #8702 states these remain in the original ignored local directory `results-local/doom/map01-v39-live-threat-guard-a07-20261009/`; I did not inspect that private directory. Record these artifacts as **not available in inspected sources**, not globally lost.

The hold can be cleared by an authorized custodian making the unchanged raw bundle available for a separate offline, read-only hash/audit reproduction, or by preserving a privacy-approved artifact manifest that lets another worker verify the claims. Until then, keep PR #8702 as a draft custody hold and preserve `formal_pass=false`, the original FAIL/HOLD, no useful scorer/task effect, and unknown physical verification. No allocation or live experiment is requested by this audit.
