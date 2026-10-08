# #3352: enforce missing retained-receipt audit checks

## Outcome and decision

**PASS_SAVED_DATA_REPAIR_SCOPED**, ordinary regression/engineering only.
The unchanged original seven frozen inputs are accepted. V2 rejects 17 altered or
missing input sets among 18 retained rows. Legacy v1 falsely accepts six discriminating
single-input mutations: whitespace changes in four receipt inputs and independent
changes to the two omitted RUN image fields. One additional trailing-whitespace
run-output mutation is already rejected by v1's line-count check.

Adopt `audit_v2.py` for future checks of this exact saved bundle after review. It adds
four frozen input byte/hash checks and two RUN image identity joins, preserving the
legacy checks. This cannot retroactively satisfy T0A's original one-shot declared gate,
prove receipt authenticity, or establish actual OS/image/container effects.

## Provenance and execution

Worker/session `01a10197-0733-77db-8e93-1eb0819290b5` (`/root`), FINAL-v5.
Scientific/engineering parent [#3352](https://github.com/Unjuno/agent-interface/issues/3352);
claim [5968882337](https://github.com/Unjuno/agent-interface/issues/3352#issuecomment-5968882337).
Source main `0e9cf1cf4a87dfbefcdf934f25503863e14af33a`; all nine external source/freeze
pins are in `SOURCE_PINS.json`, including Git blobs and SHA-256. All checked hashes
are compared against the original `AUDIT_FREEZE.md`, not regenerated caller input.
Original #7020's 19 files are unchanged. No consumed build/run/auditor allocation was
replayed: saved-data regression subprocesses are explicitly ordinary checks.

Execution host: dedicated Linux x86_64 container `330408f38db5`, kernel
6.18.44, glibc2.41, CPython3.12.14. No image provenance claim for this host;
this is not WSLc/OrbStack parity evidence. No dependency install, GUI/GPU/model,
shared runtime, resource lease or physical input. Initial filesystem approximately
30 GiB free; tiny serial subprocesses, no throughput/latency interpretation.
N, common deadline and actual model/effort settings are unconfirmed and not reset.

`matrix.json` retains the first 17-case ordinary matrix, with exact argv, child PID,
UTC start/end, stdout/stderr, exits and seven input hashes per row.
`additional_case.json` adds the discriminating inline-JSON whitespace case without
replacing or rerunning any first row. Across these outputs: v1 CLI checks=8,
v2 CLI checks=18. `run_regressions_v1.py.txt` and
`additional_construction_script.py.txt` retain the literal launch sources;
`EXECUTED_SOURCE_IDENTITIES.json` binds the source snapshots. New import-safe
`run_regressions.py` differs only by a main guard after collection.

`CHECKS.json` retains four later commands/PIDs/UTC/streams/exits: unittest5/5 normal,
unittest5/5 optimized, raw-only verification normal and optimized (all exit0).
The suite tests seven independent hash guards, both image joins with construction-only
hash overrides, unchanged positive output, all saved rows, and six effective copied-matrix
corruptions. These overrides are private tests; the production CLI accepts no replacement pins.
A separate raw-only checker imports neither auditor, verifies frozen table/source hashes,
exact mutation bytes, roster and first decisions. It is a separate implementation by
this author, not a nonauthor content vote or proof of original execution authenticity.

## H / T / D / C / U

- H: enforcing the declared frozen receipt hashes and image joins rejects the omitted
  integrity violations while leaving intact saved inputs accepted.
- T: saved-input single-file whitespace/image mutations, missing-input and source controls;
  independent raw-only reconstruction and effective copied-matrix controls. Ordinary repair
  checks only; finite assignments, not independent statistical samples.
- D: accept original, reject every declared altered/missing case; image joins must reject
  even when the test locally updates RUN's expected hash. Preserve all first failures.
- C: JSON/parser shape checks can already reject some byte changes; the run-tail control
  exposed this and is reported separately. Hash checks are stronger exact-byte binding,
  not an authentication mechanism or a general semantic validator.
- U: saved receipts may be incomplete, fabricated or untrusted. V2 does not certify
  generation, hidden runtime state, actual cleanup, cap/OOM relief, application migration,
  performance, correct natural-language claims, or arbitrary future receipt schemas.
  Existing legacy scalar/type/schema limits outside these pins are not generally repaired.

## First failures and construction repairs

The first raw-only verifier expected six v1 false accepts from the initial17 rows and
failed at its acceptance assertion. Actual count was5 because appended run whitespace
adds a third line. `FIRST_CHECK_FAILURE.txt`, unchanged matrix/cases and the literal
`verify_repair_v1.py.txt` retain this. A distinct inline whitespace control was then
executed (one v1 + one v2 check); the verifier now expects18 rows and six false accepts.
No original input or first decision was overwritten.

The first five-method test run had one failure: its control-effectiveness assertion
used Python dict equality, making 0 and False compare equal before the strict raw-checker
was called. The test was corrected to compare serialized JSON. Original test source and
`TEST_FIRST_FAILURE.txt` retain the failure. Full first verifier/unit failure tool streams
were not separately persisted; these two files are summaries, not fabricated raw receipts.
Final command streams are retained in `CHECKS.json`. Explicit checker exceptions preserve
validation under `python -O`.

An initially overbroad checkout was interrupted by this worker and only its identified
Git subprocesses terminated; a narrow sparse checkout then completed. No other worker,
source checkout or allocation was altered. This is an environment setup correction.

## Publication and handoff

Dedicated branch `research/3352-receipt-audit-v2-01a10197`; unique additive package.
No runtime import, test-discovery registration, workflow or default changes.
Only a sorted navigation row is added to the existing analysis index. `MANIFEST.json`
closes the local packet except itself. Optional remote CI is not a required wait here;
local tests and diff/provenance/index checks are the author verification.

Main reflection is pending actual existing nonauthor committee acceptance/two content
votes, current-base composed-tree confirmation, live required rules/checks and one
conditional history-preserving apply. No reviewer, approval, lock, CAS or main send is
claimed. Original owner's source/science remains theirs. Shared leases/input: none.
The next finite action is review and integration of this saved-data repair, not a retry
of T0/T0A or a new runtime resource request. Broader #3352/#57/#59 remain open.

Publication preflight: ordinary sparse staging first omitted the new packet; the unpublished commit was amended to include it. Whole-diff whitespace warnings occur only in seven deliberately whitespace-mutated case inputs; those original bytes are retained. Non-case diff --check passes. Publication branch was rebased without conflict onto effc43f8bd11f20f83c3410101c04f31c0c353f7; the original19-file dependency package has no intervening diff. Source intake pins and results remain on0e9cf1c. This is author applicability confirmation, not final nonauthor composed-tree approval.
