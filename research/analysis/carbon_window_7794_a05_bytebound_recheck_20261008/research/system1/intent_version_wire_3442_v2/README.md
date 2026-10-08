# Intent/evidence version wire contracts — #3994 / #4009

**Result: PASS_VERSION_WIRE_BOUNDARY_SCOPED for #4009.**
The first #3994 attempt remains STOP_OUTER_TOOL_TIMEOUT_PARTIAL, never relabeled.
This is an additive finite protocol check, not a model-quality result or runtime patch.

## Observed boundary

A proposal version `9007199254740995` differs from independently retained current
version `9007199254740996`. In a proposal-only Node JSON round trip it becomes
`9007199254740996`; both the extracted legacy helper and a strict int64 receiver
then return PROPOSE. Direct Python returns YIELD. Receiver typing cannot recover
identity discarded by a prior representation conversion.

| Policy | PROPOSE for originally unequal messages, in the fixed 132-record matrix |
|---|---:|
| LEGACY | 6 |
| INT64_RECEIVER | 6 |
| SAFE53_RECEIVER | 0 |
| SAFE53_INGRESS_AND_RECEIVER | 0 |
| DECIMAL_STRING_RECEIVER | 0 |

Zero inequality-loss count does not mean full original-type validation: receiver-only
SAFE53 accepts two whole-message cases whose original `1.0` tokens normalize to `1`.
Source numeric-domain checking rejects those before conversion. Safe53 permits exact
nonnegative Python integers up to 9007199254740991; it rejects high numeric versions,
so does not preserve their liveness. The separate canonical ASCII decimal string
contract supports values through 9223372036854775807 without Number conversion.
It preserves high-version equality/inequality and rejects noncanonical/range-invalid
strings. These policies have different input domains; counts are not deployment
error rates or model accuracies. PROPOSE is authority-neutral, not action admission.

## Execution and verification

One fresh allocation: 44 frozen wire inputs x 3 transports x 5 policies = 132 Python
workers, 88 actual Node conversions, 660 classifications. Eleven predetermined batches
of 12 ran once, every batch exit 0; no replacement, tuning or predecessor pooling.
Raw-only independent audit: PASS, zero errors, eight corrupted copies rejected.
Separate process-retention audit: PASS across all 11 batches and exact concatenation.
All output flags: authority=none, input_dispatched=false, model_calls=0.
Independent means separate implementation/process, not a second human/host review.

Environment: provided Linux x86_64 container, CPython 3.13.5, Node v22.16.0,
standard-library Python. Docker CLI absent; no Docker/OrbStack/image-attestation claim.
No training, GPU, provider, GUI/input, network experiment or production mutation.
Node is a controlled bridge fixture, not asserted to be in the deployed runtime.

Raw SHA256: `2d8f0c280784fc7412b889a0ebc581ad1d36aaa67edda5f1611a142abbd15cf8`
(128,552 bytes). The frozen raw auditor and retention checker reproduce byte-identical
outputs after a fresh unpack. Five package corruption/overwrite controls pass;
actual commands/return codes are in [PACKAGING_CHECK.json](PACKAGING_CHECK.json).

## Immutable predecessor and public freeze chronology

#3994's single monolithic invocation hit the container tool timeout. It retained
49/132 rows, raw SHA256 `42a28e0ffb2c5d18c3a8a5ecaf89302c156abd28d938bce8e8628e65f5b520e5`.
The outer exit and END.json are absent. Its full formal audit was not run. Those
49 rows remain a separate STOP and are not pooled into #4009.

#4009 changed only orchestration. Its fixtures/classifiers/worker/raw auditor are
byte-identical to #3994; 132 fresh cases were run under a new ID. Public hash manifests
were committed/read back before each allocation at 97282093499e865a2d9538815c77affda47a57a6
(v1) and 858c2ace743ca2b822d953b8deebfb190932beda (v2). Those commits contain hashes,
not full source bytes; complete source bytes were first published with this bundle.
Original intake main: 485f0edc51fee27bf6a8ef21cbfb78612805c4c1.
Only INTENT_IDS and intent_gate were extracted from #3442's pinned runner; its
training-triggering module was never imported/executed. Old model FAIL is unchanged.

## Complete evidence and read-only reproduction

The eight base64 fragments encode one 33,612-byte xz archive with 134 files
(484,979 member bytes): full v1/v2 source, fixtures, H/T/D/C/U, variable/unit table,
analytical argument, construction, stopped raw, complete raw, every batch receipt,
auditors and detailed REPORT.md. EVIDENCE.json binds fragments, archive and member
manifest. Fragments were checked against the local originals by Git blob ID.

From a checkout, choose a NEW output directory:

```sh
python -B research/system1/intent_version_wire_3442_v2/unpack.py /tmp/intent-wire-review
python -B /tmp/intent-wire-review/v2/audit.py /tmp/intent-wire-review/v2/formal
python -B /tmp/intent-wire-review/v2/verify_batches.py /tmp/intent-wire-review/v2/formal
(cd /tmp/intent-wire-review/v2 && python -B -m unittest test_contract test_batches)
```

Unpacking verifies hashes and member paths before writing; it never runs experiments.
Do not invoke either consumed formal allocation. v2/SUCCESSOR_PLAN.md overrides only
the monolithic orchestration described in the copied original PLAN.md. Assertions
must stay enabled for verify_batches.py; it explicitly refuses optimized Python.

## H/T/D/C/U and bounded roadmap

H: deserialized equality need not preserve original version identity. T: the fixed
132-case actual-interpreter matrix above. D: exact oracle/byte/source/order/exit
reconciliation, all directed witnesses and corruption gates; all passed. C: domains
are explicit alternatives and source validation precedes only the tested conversion.
U: no authenticity, epoch ownership, observation freshness, lease, check/use atomicity,
arbitrary parser, model quality, general reliability, latency or production claim.
No statistical confidence, combined u_c or coverage factor k is estimated from fixed
cases. Versions are dimensionless (SI unit 1); clocks are not version identifiers.

Intake, construction, public hash freeze, execution and independent audits are complete.
PR checks, merge and main readback are separate delivery gates, not inferred here.
#3442 and the global ROADMAP stay open. No learned component or production default
is promoted. Numerical representation, protocol serialization and distributed
state identity are the three transfer areas; deployments need their own exact gates.

The prior chat-local intent-relative learning FAIL was re-audited without training
(56 manifest entries, eight corruption controls, 17 retention checks). Its complete
6.2 MB ZIP remains a conversation attachment and is NOT contained here or claimed
fully delivered to GitHub. #3994 records that remaining publication gap.

Primary references: [RFC 8259 section 6](https://www.rfc-editor.org/rfc/rfc8259#section-6),
[Python 3.13 JSON](https://docs.python.org/3.13/library/json.html),
[ECMAScript safe integers](https://tc39.es/ecma262/multipage/numbers-and-dates.html#sec-number.max_safe_integer).
Existing numeric semantics are not presented as a newly discovered Node defect.
