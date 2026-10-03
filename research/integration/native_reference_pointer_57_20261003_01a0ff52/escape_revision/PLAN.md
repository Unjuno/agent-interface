# Original JSON Pointer escape validation: ordinary regression repair

Worker `01a0ff52-5884-7172-a388-d9ac576e13dd`, FINAL-v5; #57 / #6874.
Responds to nonauthor review 5398544815 / inline 4171306428. No formal
allocation, backend, model, GUI/input, GPU, container or shared lease.

H: validating original tokens left to right rejects adjacent malformed tilde
escapes, preserving RFC 6901 sections 3–4 decoding order and exact output.
Primary specification: https://www.rfc-editor.org/rfc/rfc6901#section-3 .

T: preserve the current source and test-first result before repair. Four
regression methods specify six invalid and six valid tokens: 18 invalid-source
cases across all three public decoders, 24 valid source/target cases, six
invalid native-multiple target cases, and all 341 strings over `~01a` through
length four against a separately expressed full-token regular-expression
grammar. This totals 389 subcases, not independent statistical samples.
Run focused normal/optimized tests, the affected CLI suites and committed
archive import checks after correction. Keep first failures and exact receipts.

D: baseline must expose the reported adjacent-escape defect. The repaired
regressions, valid controls and immutable caller inputs must all pass. Missing
coverage, unexpected refusal of `~01`/`~001`, or remaining acceptance of invalid
original syntax is FAIL/HOLD. Do not relax tokens or erase the first failures.

C: validation by deleting escapes rewrites neighboring characters and can
hide an originally invalid tilde; changing only the decoding order would not
repair that validation. The old native-v2 helper already contained this gap.
The shared-resolver repair exposed it in the other two public paths.

U: finite short-token grammar and explicit dictionary source/target cases;
no broad Python-object/container, concurrency, backend effect, authority,
performance or platform claim. Test and repair have one author; prospective
independent content review remains required. Historical pointer and marker
raw/source witnesses remain unchanged and source-bound to their earlier heads.
