# Core integer applicability — successor allocation 02

Issue #3442 remains open. This is a new, additive allocation; it does not
rewrite or claim completion of allocation 01.

## Recovery boundary

Remote branch `research/core-integer-applicability-3442-20260922` contains only
the original one-file FREEZE relative to current main. Its Issue record says
formal execution never started, and the frozen runner, auditor, tests, and
environment bytes are unavailable. Reconstructing those bytes from their old
hashes would not recover that allocation. The original branch and freeze stay
unchanged.

The preceding older 2026-09-22 refs #3987, #4064, and #4059 already have
Issue-reported executed allocations, but their exact runner/raw/audit payloads
are missing from the corresponding remote branches and current main. Their
Issues record publication HOLD and explicitly rule out rerunning the consumed
allocations. They are not treated as recoverable scientific result bundles.
Among the next chronological frozen-but-unrun refs checked, #3442 is therefore
the earliest eligible for a fresh, explicitly scoped successor allocation.

The predecessor freeze says “12 fields × 15 × 2”, but the current-main
`runtime/core_v1/contract.py` has **13** integer-leaf validation sites. This
successor tests all 13 rather than silently leaving one out. Its denominator
is therefore 13 × 15 × 2 = **390** rows. This is a scope-explicit successor,
not a relabeling of the predecessor's unexecuted 360-row proposal.

## H — hypothesis

At the current-main `validate_program` / `admit_program` boundary, every exact
Python `int` within each field's declared inclusive bounds is preserved and
accepted when unrelated freshness inputs match. `bool`, `float`, `str`, and
`None` are refused even when numerically suggestive; integers immediately
outside the declared bounds are refused. Python-direct construction and one
ordinary `json.dumps`/`json.loads` round trip yield identical typed values and
decisions for all 13 fields.

## T — bounded experiment

- Frozen code base: main `40885011a5d8e15ab10bb6cc0e8eef65661718ee`.
- Candidate: the unmodified current-main `runtime/core_v1/contract.py`; its
  Git blob and byte-level SHA-256 are in `FREEZE.json`.
- Fields: `source.observation_seq`, `source.binding_revision`,
  `authority.expires_at_ns`, `activate.timeout_ms`, `pointer_move.x/y`,
  `scroll.dx/dy`, `observe.x/y/w/h`, and `wait_update.timeout_ms`.
- Per field, test 15 fixed values: six exact in-range integers (`lo`, `lo+1`,
  `lo+2`, `hi-1`, `hi`, floor midpoint); adjacent out-of-range integers
  (`lo-1`, `hi+1`); `False`, `True`; integral floats at `lo`, midpoint, `hi`;
  the string form of `lo`; and `None`.
- Modes: direct Python value and one canonical standard-library JSON encode /
  decode. The full input program, wire bytes where applicable, observed typed
  value, validation exception/index, admission receipt, and hashes are kept
  per row.
- Fixed controls: one otherwise-valid inert program; a declared all-supported
  capability manifest; `now_ns=0`; current observation/binding values equal
  the program values when they are exact integers. No backend is contacted.
- Run `study.py` once as a candidate process. Only candidate exit 0 permits one
  separate `auditor.py` process. The raw-only auditor imports neither the
  candidate runner nor runtime code; it uses a separately transcribed finite
  type/range oracle, checks all rows and paired modes, and applies 10 mutations
  to copies of raw evidence. No retry, re-freeze, or candidate rerun.
- Environment: host-local macOS arm64 / CPython 3.13.14, stdlib only. No
  Docker/OrbStack container, GUI, input, provider, model, or network call is
  part of this allocation. No shared container slot is requested or claimed.

## D — decision

`PASS_CORE_INTEGER_BOUNDARY_SCOPED` requires exactly 390 unique rows; for each
mode 195 rows comprising 78 accepted and 117 refused; across both modes 156
accepted and 234 refused (182 type refusals and 52 range refusals); exact
field/value/type/error/index/admission agreement; direct/JSON parity; frozen
main and source identity; candidate and auditor exit 0; and all 10 corruption
controls rejected. Any completed, provenance-valid decision mismatch is
`FAIL_CORE_INTEGER_BOUNDARY_EXPECTATION`. Missing rows, source drift, or process
integrity failure is `STOP/HOLD`, not a scientific FAIL. The allocation is
one-shot; no formal retry or replacement is allowed.

## C — controlled factors

Only one numeric leaf value changes per row. Program schema, all other values,
operation ordering, declared capabilities, admission time and matching source
versions are fixed. The two modes differ only by the single standard-library
JSON round trip. The manifest is an inert fixture, not a probed backend.

## U — limits

This is a host-local CPython 3.13.14 macOS arm64 result, not Linux/x86_64 or
container evidence. It studies only values reaching this post-deserialization
validator boundary. It says nothing about upstream CLI/provider conversion,
native ABI, live backend capability, GUI/input safety, task effect, production
adoption, performance, model quality, or user benefit. It proposes no runtime
change; the applicable disposition, if the gate passes, is only
`DO_NOT_INSERT_BINARY32_CELL_GUARD_AT_THIS_INTEGER_BOUNDARY`.

## Commands

Construction suite (excluded from the formal 390 rows):

```sh
python3.13 -m unittest \
  research.system1.core_integer_applicability_3442_v2.test_study \
  research.system1.core_integer_applicability_3442_v2.test_auditor
```

One-shot candidate command:

```sh
python3.13 -m research.system1.core_integer_applicability_3442_v2.study \
  --out research/system1/core_integer_applicability_3442_v2/results/formal-01/raw.jsonl \
  --main-sha 40885011a5d8e15ab10bb6cc0e8eef65661718ee
```

Run the independent auditor as a separate process only if the candidate exits
0:

```sh
python3.13 -m research.system1.core_integer_applicability_3442_v2.auditor \
  --raw research/system1/core_integer_applicability_3442_v2/results/formal-01/raw.jsonl \
  --out research/system1/core_integer_applicability_3442_v2/results/formal-01/audit.json \
  --main-sha 40885011a5d8e15ab10bb6cc0e8eef65661718ee \
  --source-sha256 4ad7e4426148688b8ece0ffbc4e95527b3697c08c84e5d0ab23a84f364574dc2
```
