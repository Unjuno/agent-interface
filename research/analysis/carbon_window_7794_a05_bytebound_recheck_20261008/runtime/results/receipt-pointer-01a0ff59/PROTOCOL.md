# Receipt pointer engineering boundary — Issue #6873

Worker `01a0ff59-0820-7c81-8ef1-f7c3e48ab67d`, FINAL-v5.
Base `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`.

H: the two legacy decoders' `int()` array traversal admits invalid pointer
aliases; sharing the existing strict pointer evaluator preserves canonical
reconstruction and rejects those aliases.

T: retain the 20-case unchanged-source reproduction and failing regressions.
After minimal repair, test the three public decoder formats on every token
of length 0–3 over the declared ten-symbol alphabet `012-+ _`, tab, Arabic zero
and fullwidth zero: 1,111 tokens, 3,333 rows. A separately written raw-only
oracle uses RFC 6901's ASCII unsigned decimal grammar, no leading zero except
`0`, and fixture array bounds. It verifies each complete reconstructed output
digest and unchanged input. Include row omission, duplicate identity, false
admission, wrong reconstructed output and source drift corruption controls.
Ordinary construction/regression validation, not a formal allocation.

D: PASS_FINITE_POINTER_GRAMMAR requires all rows, zero wrong admissions/refusals,
exact reconstruction, all inputs unchanged and five rejected corruptions.
Retain every earlier failure. The focused public-decoder regressions and relevant
existing receipt/review/presentation suites must pass before delivery.

C: producers already emit canonical pointers. This repairs malformed-input
decoding; it does not establish that normal compactors corrupt evidence.
U: a finite token corpus is not arbitrary JSON/schema validation, duplicate-key
rejection, arbitrary-length proof, an OS/GUI test, task success or performance.

Source/probe/auditor hashes are fixed in FREEZE.json before the finite check.
No GUI, physical input, model, WSLc/container, GPU, shared lease or main write.
Output budget 1 MiB. The source change is a strict evaluator reused across receipt
formats; no action admission, native backend or capture behavior is changed.

Primary specification: https://www.rfc-editor.org/rfc/rfc6901.html#section-4
