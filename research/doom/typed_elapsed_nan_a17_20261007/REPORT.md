# Typed elapsed metadata: NaN rejection boundary

Issue #8249, parent #59. **PASS_TYPED_ELAPSED_VALIDATION_SCOPED** for one
48-row engineering matrix. This is an additive evidence-and-patch handoff;
`research/doom/doom_typed_observation_v1.py` in the shared tree is NOT changed.
No game, native input, model call or live observation was executed.

## Finding and actual outcomes

The original negative out-of-tolerance predicate accepts NaN because ordered
NaN comparisons are false. The tested one-line patch requires positive
consistency instead. It preserves the finite-input outcomes and leaves the
integer-nanosecond freshness guard unchanged.

| Per 48 input rows | Original | Candidate |
|---|---:|---:|
| Snapshot accepted | 14 | 12 |
| Snapshot rejected | 28 | 30 |
| Not invoked: strict decoder refused | 6 | 6 |
| Downstream VALID_CURRENT | 7 | 6 |
| Downstream REJECTED_STALE | 7 | 6 |

Only the two permissively decoded NaN rows change snapshot admission. At
50ms age the original returns VALID_CURRENT; at200ms it returns REJECTED_STALE
against the unchanged100ms age budget. Therefore this does NOT show a bypass
of that freshness guard. All returned validity results deny input authority.
The strict decoder rejects NaN and both infinities before either module.

Normal finite10/10.0 and the in-tolerance10.0000000005 values are preserved;
out-of-tolerance10.000000002, infinities and five wrong-type/shape controls
(null, true, quoted10, empty list and empty object) are refused as specified. The twelve-token schedule is authoritative in PROTOCOL.md
and run.py. Counts are finite coverage, not probabilities or performance.

## Source-first chronology and executed commands

Intake main: 5d48c8beb7e0380da4ab3e15cc93cde111d74749.
Complete original subject Git blob930e1c78511b57999a0a2176cb94a31a32d166a8;
complete dependency31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e.
Both modules were loaded normally, with no extracted-function or import stub.

Excluded RED: six methods, five pass and one intended NaN-refusal failure.
Excluded GREEN: six methods pass after the one-line candidate change.
Original stdout/stderr and exit1/exit0 records are retained.

Public source commit73a9c7a052ac4ed53400ba53fe4788857e3c9a31 and Issue comment
6019720681 preceded the only retained invocation. Complete ten-file public
subtreee8441fbd1fbc91bac2ab7f4cb57ad96be244e17e matched the local Git tree.
The candidate is reconstructed from the published original and exact patch,
with its full resulting byte hash fixed in FREEZE.json.

`python -B run.py results/raw.json`:48 rows,84 module calls, workerPID808,
supervisor798, returncode0, no timeout, empty stderr. Retained raw132303 bytes,
SHA256 ab5a5e5a01d5401c943e4957c1620b424a355f7a752667e7999d1b7ae71902cb.

Separate `python -B audit.py results/raw.json --controls`:48 rows, errors[],
six effective mutations rejected, PID875/supervisor865, returncode0, no timeout,
empty stderr. Audit SHA256
b9f338f686868ebbd91fcfb29b748e05f3c836e31973151e2c01e0482afa4029.
All ten frozen file hashes still match. First-outcome comment6019794274
preceded packaging. Matrix retries/replacements/pooling/tuning:0.

## H / T / D / C / U

H: a positive consistency requirement closes the NaN metadata validation gap.
T: twelve duration tokens x two decision ages x two JSON decoders; complete
original/candidate modules plus unchanged downstream validity evaluator.
D: all48 exact source/wire/outcome rows and process exits; finite parity;
NaN discriminator; strict-decoder no-call boundary; unchanged stale refusal;
separate raw-only Decimal oracle and6/6 semantic/provenance controls.
C: default Python JSON permits nonstandard constants; ordinary producer
output is finite. This is a corrupted/direct-call input contract test, not
proof the live producer emits NaN. The field is redundant timing metadata.
U: no full V39 startup, GUI/game effect, physical release, model decisions,
latency/tokens, clock calibration, arbitrary numeric magnitude/Python objects,
image authentication, natural fault rates or product acceptance.

Supplied private Linux x86_64/CPython3.13.5/Pillow12.3.0 environment. No
Docker/WSLc/OrbStack image attestation or shared-workstation/GPU allocation.
No installation or experimental network. Direct GitHub DNS failed locally;
GitHub MCP supplied source/publication. Same-author separate implementation
and process auditing are NOT independent human review or repository CI.

## Retention and read-only reproduction

The four results.xz.b64 parts plus PACK.json preserve15 exact original files:
construction RED/GREEN records, raw matrix, original audits, actual process
receipts, derived summary and original source readback. The ten public source
files plus reconstructed candidate and those15 members account for all26
files present at first result packaging. No source/raw record is a placeholder.

From this study directory (Python3.13 and compatible Pillow installed):

```sh
python -B verify_saved.py /tmp/typed-elapsed-a17-new-directory
python -B test_restore.py
```

The destination must not exist. The verifier restores bytes, reconstructs the
fixed candidate, runs only the saved-data auditor and six candidate regression
methods, and compares the audit output byte-for-byte. It NEVER runs run.py.
Six packaging tests cover intact restoration plus five refusal cases.
The restorer assumes a trusted/quiescent parent directory; hashes establish
integrity, not authenticity or a general adversarial filesystem sandbox.

Post-result packaging first recorded a missing-module test setup failure before
the restorer existed; that is not an effective corruption control. Its logs and
the later six passing tests are retained in PACKAGING_CHECK.json. This did not
change source freeze, scientific raw or outcomes. Fresh extraction reproduced
all15 member bytes, identical original audit output and6/6 candidate regressions.
REVALIDATION.json records the exact checks. No scientific rerun occurred.

## Integration / remaining roadmap

Research execution and complete local/public handoff are distinct from adoption.
The shared source is unchanged; candidate.patch is a tested proposal only.
A genuine nonauthor review and applicable current-head CI/policy/ownership
checks must precede a permitted merge. Do not self-approve, simulate consensus,
retrigger another worker's allocations, or merge on this component PASS alone.
Keep the owned branch while PR/review/custody depends on it. #59 and the broader
ROADMAP remain open; the live threat-control gate was not consumed or satisfied.

Publication staging: two unreferenced zlib transport-tree attempts contained
assistant transcription errors; neither was committed or attached to the
branch. Smaller XZ text fragments replace only the transport encoding. Original
raw and audit bytes remain fixed. No blocked operation was retried.
