# Issue #4369 — operation enum type compatibility

Intake main: `4a1f3957e91b412a64769199f78f2c4b0102d28b`.
Engineering repair for #3850/#2789, not a new scientific algorithm.
Branch: `engineering/program-enum-types-20260925-e9q4`.

## H / T / D / C / U

H: three local string checks turn JSON array/object mistakes into existing
indexed ContractError / INVALID_PROGRAM refusals, without accepting any new
JSON program or changing valid/scalar-invalid behavior.

T: exactly 140 distinct supplied cases, evaluated on two isolated source trees.
For each of three contexts (plain; repeat prefix; mixed text-gap/repeat prefix),
evaluate pointer_move.frame, observe.frame and pointer_button.button. Each
field receives 11 invalid values (four lists/objects, seven scalar examples)
and all its valid enum strings (3,3,5). This gives 132 cases. Eight additional
controls cover expired, stale observation, stale binding, unsupported capability,
permission required, coordinate unsupported, earlier error precedence and
129-operation overflow. The first three contextual source indices are 0,1,2;
expanded indices are 0,2,5. No expansion algorithm or location helper changes.

One worker per arm calls exact validate_program, admit_program and the unchanged
inspect_program. Eight case IDs per arm (0,11,44,55,88,99,138,139) additionally
run the actual validate_program.py file entry in fresh processes over actual
JSON files. PYTHONPATH points at the corresponding complete core source tree;
DISPLAY, WAYLAND_DISPLAY and XAUTHORITY are removed. We intentionally do not
exercise `python -m runtime.cli_v1...`, whose package initializer imports a
separate dispatch facade. There is no replaced initializer or native stub.
Normal core __init__/platform_probe imports are retained byte-identically.
The initial discovery probe preceded installing core __init__ locally and is
not the retained normal-package run. Root runtime is a namespace package.

Construction: 8 new unit methods; excluded 9-case/2-worker/4-file-entry smoke
and raw-only oracle (269 checks, errors=[]). No complete 140-case matrix has
run before source/gate publication. All observed construction output is kept.
Source copies are checked by Git blob identity; only three existing core lines
change. One retained matrix, no retries/replacements/exclusions/tuning. Per-child
10-second timeout; kill/wait only the owned child on timeout and retain STOP.
No production backend/session, GUI, key/mouse, model/provider or experiment
network is invoked. No synthetic acceptance is a server-issued lease.

D: complete 140-case/280 API rows and 16 file-entry receipts; both API workers
and all file entries have actual exits/stderr; input and source nonmutation.
Baseline must expose exactly 36 TypeErrors each at core validation/admission;
candidate must expose zero, with 101 static-invalid and 39 static-valid rows.
All 104 non-TypeError baseline rows must be byte-equivalent to candidate rows.
Of the 39 static-valid rows, six must remain refused by admission controls;
only 33 are accepted against a synthetic all-capabilities manifest. Static
validity is not runtime readiness or task success. Every static report remains
authority-neutral. Full expected output dictionaries and source positions are
reconstructed by audit.py without importing runtime, worker or corpus builder.
Ten effective rehashed/copied evidence mutations must be rejected normally.
A complete discrepancy is FAIL; missing source/raw/exit or ineffective controls
is HOLD/STOP. PASS_PROGRAM_ENUM_TYPE_COMPATIBILITY closes this repair only.

C: acyclic JSON-derived built-in values and a valid synthetic manifest. Custom
Python hash/equality, malformed backend manifests and concurrent mutation are
not covered. No generic TypeError catch is added. Existing messages, earlier
error precedence, state tracking, capability and freshness checks are unchanged.
The type-first check is local, before each membership operation; it does not
reorder fields across operations. Existing expansion-stage Issue #4348 and
presentation #4350 are distinct. No blocked-source/capsule is reused.

U: same Linux x86_64/CPython3.13.5 execution container; Docker/gh absent, no image
attestation. No GUI/model usefulness, retry benefit, latency/token measurement,
production safety, arbitrary-JSON totality or external human review claim.
Timestamps only establish bounded process ordering. No calibrated combined
uncertainty or coverage factor is invented. Native behavior is not exercised.

## Accepted-domain argument (JSON values only)

The two coordinate enum sets and button enum set contain only strings. A JSON
string therefore uses exactly the same membership test before and after this
change. A JSON null, boolean or number cannot equal a member string; it remains
invalid with the same ContractError/message/index. JSON arrays and objects
previously raised TypeError during hashing; the new first operand is false,
so short-circuit evaluation skips hashing and the existing _need raises the
same field-specific ContractError as other invalid values. No invalid value
becomes valid. With an identical valid program, all later state/capability/
freshness checks execute unchanged. Error position now flows through the
existing per-operation exception handler and static source map; no new mapper
is introduced. This argument is not extended to arbitrary Python objects.

Primary specification: Python 3.13 built-in types (Boolean short circuit,
set membership) and glossary (hashable), docs.python.org. Code measurements
are local evidence; documentation is implementation background.

## Variable / unit register

| Field | Meaning | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| id | corpus row identity | 1 | fixed enumeration | integers 0..139 | integer scalar |
| source_operation_index | original operation position | 1 | zero-based list position | when recorded | integer scalar, not bool |
| expanded_operation_index | compiled operation position | 1 | zero-based expanded list | 0..127 when valid location | integer scalar |
| start_ns/end_ns | process invocation brackets | s, stored ns | host monotonic_ns | same clock, ordered | integer scalar |
| now_ns/expires_at_ns | synthetic admission clock inputs | s, stored ns | explicit fixture values | not real lease issuance | integer scalar |
| gap_ms/timeout_ms | program delay arguments | s, stored ms | unchanged compiler input | bounded core contract | integer scalar |
| x/y/w/h | screen geometry inputs | dimensionless pixel counts | fixture rectangle | current tests only; no physical length | integer scalar |
| sha256 | byte identity | none | SHA-256 of exact bytes | integrity, not authentication | hexadecimal string |

Unit check: operation counts/indices are dimensionless. Host ns and synthetic
ns are never subtracted from one another. Millisecond operation arguments are
not treated as measured process durations. No timing benchmark is reported.

## Roadmap / ownership

Pinned defect -> excluded construction -> public full source/freeze readback ->
one retained matrix -> independent raw oracle and ten controls -> additive tests
and evidence plus three-line core PR -> applicable exact-head CI/scoped review ->
qualified merge/main readback. Historical artifacts stay immutable. Broad #3850,
#57 and ROADMAP remain open. Only owned dependency-safe branches may be deleted.
