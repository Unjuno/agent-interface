# Post-result scalar audit correction

Read this note together with the retained [first report](REPORT.md).
The original proposal was withdrawn before any observed vote in
[author HOLD](https://github.com/Unjuno/agent-interface/pull/6928#issuecomment-5965821648).
The frozen v1 auditor accepted rejoined boolean/float ordinal and native-I/O
corruptions. Its original method PASS describes the checks actually exercised;
it does not establish the missing strict scalar checks. All original evidence
and the first v1 proposal remain historical, recoverable records.

The first two accepted corruptions are preserved in
[SELF_CHALLENGE_FIRST.json](supplement_v2/SELF_CHALLENGE_FIRST.json).
Expanded ordinary regression found eight accepted, independently rejoined
copied-row controls: boolean sample ordinal, float native read request, wrong
integer native read request, boolean sink count, float prequeue byte count,
float read limit, float clock source-line ordinal, and integer readiness flag.
Each copied saved row was rewritten and its artifact length/hash recomputed;
v1 returned no error, so acceptance was not obscured by a stale artifact join.
The copied-data mutation definitions and results are public. No fake native
result was substituted for the original result.

The additive [auditor_v2.py](auditor_v2.py) imports the frozen v1 data verifier
and adds strict integer bounds for sample ordinals/timestamps, event ordinals,
native byte counts/requests/limits, sink and budget counts and recorded stats;
read requests must be65536, and the effective limit must match the frozen deck.
Readiness/closure/stat flags have explicit boolean checks; wait durations are
finite nonnegative numbers and the stdin rate has its original float type.
These are supplementary recorded-scalar checks, not a new independently authored
full oracle, adversarial provenance proof or exhaustive malformed-input parser.
The existing v1 native/scorer/effect/schedule joins remain in force.

Four ordinary [regressions](scalar_checks_v2.py) failed with eight named
subtest failures before repair. The original pre-repair supplement and complete
RED logs are preserved under [supplement_v2](supplement_v2/checks-red.receipt.json).
After repair, all four methods pass normally and under `-O`; eight specific
copied-row controls reject for their required scalar/value reason. The original
ten directed controls still reject. The first v1 AUDIT object is reproduced
exactly, and all16 original rows pass the supplementary checks with the same
outcomes. See [AUDIT_V2.json](supplement_v2/AUDIT_V2.json) and the actual
[retained-data receipt](supplement_v2/retained-reaudit.receipt.json).

This repair was constructed **after** the formal result. It is not part of the
preregistered freeze, a second formal audit allocation, or an independent
nonauthor review. Only ordinary functions over retained JSON/files and copied
temporary data were invoked. No candidate, native pipe, clock assay, VM,
formal auditor entry point, GUI, game or model was replayed. Timing/case/threshold
definitions were not changed, and no failed row was removed. V1 limitations,
the earlier #6924 overlap, and the absence of live game/model feedback remain.

All125 original [manifest](PUBLIC_MANIFEST.json) entries and the original
manifest bytes remain unchanged, including candidate/auditor/deck/protocol,
six copied source files, raw, individual artifacts, first construction failures
and receipts. All14 execution freeze pins remain equal. The additive
[PUBLIC_MANIFEST_V2.json](PUBLIC_MANIFEST_V2.json) covers those original files,
the original manifest and this supplement; it excludes only itself. It does
not replace or rewrite the frozen manifest. RED/ordinary-check logs containing
the private source path use literal `{OWN_SOURCE}` substitution and retain both
original-private and public-derivative hashes in each receipt. Empty/unmodified
logs have identical hashes. This is explicit publication processing, not an
authentication assertion.

Ordinary retained-data commands, from this package directory:

```sh
python -B scalar_checks_v2.py -v
python -B -O scalar_checks_v2.py -v
python -B auditor_v2.py /a/new/output/path.json
```

The output command creates a new file exclusively. These commands do not launch
the producer or consume the frozen native allocation. Helpers have no default
test-discovery filename; source/runtime/workflows are unchanged. Nonauthor
content review must bind the corrected head/digest/epoch and include this
historical correction. A v1 vote cannot be converted. Exact current-base/tree,
requirements and conditional application remain separate from content review.
