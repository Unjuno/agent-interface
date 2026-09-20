# Issue #3588 — sequence-guard construction result

## Result

`PASS_CONSTRUCTION_PREFIX_ORACLE`: the actual #3518 candidate from main was byte-compared with its pinned source and reproduces the known bug; a sequence-monotone candidate variant agrees with an independently written prefix oracle over 9 deterministic traces and 27 event prefixes. The tests reject three mutations: removing the sequence guard, mutating replacement state before validating sequence, and suppressing a previously emitted edge using a future revoke. No GTK fixture, model, or GUI input was invoked (0 formal GUI invocations).

The upstream candidate's delayed-replacement trace ends at generation 1 and emits `old-after-rollback` after the newer generation 2 replacement had already been processed. The guarded variant rejects the delayed replacement, remains at generation 2, and refuses the old-generation observation. It also refuses delayed same-generation observations/revocations by a global stream sequence watermark while preserving a valid newer-generation rising edge and valid revoke behavior.

`LAST_MESSAGE` and `MESSAGE_COUNT` were checked as distinct controls: on duplicate true arrivals they yield `[x2]` versus `[x1, x2]`; on true followed by delayed false they yield `[]` versus `[true3]`.

## Reproduction record

- Upstream `main`: `e1d9c073cdaed1a5eedf602f5959d83d39804f2b`
- Exact candidate Git blob: `37bb7b271b099ccb10a594dbe00faa5bf618099b`
- Candidate source SHA-256: `1f55427d0045b16d843f62cb5824c85a45b48fab3c1518fa3cade35296ec4efc`
- OrbStack image: `sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916` (`linux/arm64`)
- Command: `docker run --rm --platform linux/arm64 --network none --read-only --workdir /src --tmpfs /tmp:rw,noexec,nosuid,size=64m -v <source>:/src:ro -v <fresh-output>:/evidence:rw <image> sh -lc 'python3 -B -m unittest -v test_sequence_guard.py && python3 -B run_prefixes.py && python3 -B audit_prefixes.py'`
- Final construction tests: 6/6 passed; independent audit: 9 traces, 27 prefixes, 0 errors.
- Prefix-ledger SHA-256: `3300e5696f1ea2d8188ad5c36766ff47dc2bdec7240c3f225becc5a1d4e648c3`
- Audit SHA-256: `6cea13aba0475d50e73946942345880e15c22ddb5bd67a2cd0c1cf3ddffd51fc`
- Source-manifest SHA-256 (post-run provenance record): `cbf087768023068dc752c9cf579e5f494d02d373abbcb127ddc97aa30cf8bbb8`

The first construction command ran all six tests successfully but exited during the summary-print step because the trace-count expression indexed a list as a mapping. The result directory already held the prefix ledger; the denominator expression was corrected and the full container command then completed with independent audit PASS. This was construction tooling only; no formal GUI allocation was consumed or repeated.

## Scope

This is finite synthetic event-order evidence for the candidate policy and a proposed correction. It does not establish GTK task-effect behavior, public runtime integration, real event-source ordering, held-key safety, live-agent benefit, latency, or production correctness. The next gate is a separately frozen GUI-effect allocation using the actual corrected policy plus an independent effect/release/process auditor; no source change should enter production solely from this construction result.
