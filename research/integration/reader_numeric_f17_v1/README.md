# #4371: preserve reader responses on JSON float overflow

**PASS_FINITE_READER_RESPONSE_ENGINEERING.** One preregistered 96-process
comparison completed, followed by a separately implemented raw-only auditor.
This is an additive research candidate and evidence record. The shared reader,
public runtime/CLI/MCP, existing workflows and predecessor results are unchanged.

## Finding and proposed change

The original reader rejects literal NaN/Infinity via `parse_constant`, but a legal
JSON exponent-form number such as `1e309` follows `float()` conversion instead.
It becomes an infinite Python float. The unchanged experimental CLI then raises
at its `json.dumps(..., allow_nan=False)` outside the read-error handler. It exits
1 without stdout, including without the otherwise valid prefix response.
The source stream is unchanged: this is response unavailability, NOT permanent
loss of retained events or a claim about a production vulnerability.

The namespaced candidate adds only `math.isfinite` in a `parse_float` hook.
Non-finite conversion raises inside the existing per-record handler, before
record append and cursor advancement. The same CLI now returns exit2 and a
structured `blocked / INVALID_JSON_RECORD` response, with the good prefix and
cursor before the offending line. It does not skip the bad record or reach the
later sentinel. No reset, replay, ACK or input authority is introduced.

Python's decoder hook contract and RFC8259 section6 distinguish syntax from
representability. `1e400` is legal JSON number syntax; the candidate deliberately
requires finite Python float representation. Underflow and rounding remain
Python semantics, not arbitrary-precision preservation. The compatible existing
error category is retained; a new numeric-specific diagnostic was not tested.

## H / T / D / C / U

H: parser-time finite conversion preserves structured response/cursor delivery
without changing other declared branches. T:16 frozen short fixtures, original
and candidate, one page32 read plus page1/saved-cursor continuation:96 actual CLI
processes. D:10 original overflow failures,10 candidate structured refusals,
38 other exact paired responses, complete input/process/source/audit integrity
and10 effective corruption controls. C:finite-range restriction is an explicit
compatibility cost; it is not a new general JSON algorithm. U:one Python/Linux
configuration and16 directed inputs, not broad parser safety, arbitrary precision,
real model recovery, live application success, timing/token gain or production
promotion. See PLAN.md for the full pre-execution contract, proof and field units.

## Retained first result

| CLI source | Calls | Normal exit0 | Structured exit2 | Unstructured exit1 |
|---|---:|---:|---:|---:|
| Exact original |48|30|8|10|
| Candidate finite-float hook |48|30|18|0|

Five overflow fixtures (positive, negative, nested object, nested array and
binary64-boundary overflow), each in full-page and saved-cursor continuation,
account for the10 changed pairs. All16 first-page pairs preserve the same prefix.
The other38 paired responses agree exactly in decoded content, including finite
maximum/subnormal/underflow/signed-zero values, quoted numeric text, literal
constant refusals, duplicate keys and missing final LF. No timing claim follows.

The original source/candidate stdout bytes, stderr, PID, argv, exit, source hashes,
monotonic brackets, all16 input streams and32 cursor files are retained. The
runner PID735 exited0, its external receipt is present, and no timeout occurred.
Each stream and supplied cursor was unchanged. All returned authority flags stay
neutral. The candidate did not turn an unknown/blocked record into completion.

Independent raw audit:1177 row/contract checks, errors=[],10/10 effective
copied-evidence corruptions rejected normally. It imports neither reader nor
runner. Overflow classification uses Decimal with an exact binary64 threshold;
finite expected payload conversion still uses Python. Independence means separate
implementation/process by the same author, not external human review or a second
JSON library. No frozen source, criterion or row changed after the first outcome.

## Chronology and exact identities

- Intake main:4a1f3957e91b412a64769199f78f2c4b0102d28b.
- Exact original reader blob:ea72c166c2cea511ea91031dfbb14563fe4e3245.
- Exact CLI blob (identical in both copies):1a97a659113666ccaa254ab2bf5dc0306e217015.
- Public source commit:e80f67a6ae9857817d4c0414cfefcb5801042c47.
- All19 public source/construction files matched the locally computed study tree
  b0a732a2a43fb6ad8b33a7fbf49fd7ecb8c316e6 before authorization comment5832550222.
- FREEZE SHA256:f8e57f4c7270c26361181b4bc3d71b40cf7d1e0d04d693a8172ae604c2e107da.
- First-outcome comment5832559146 preceded packaging.
- RECORDS.jsonl:132312 bytes, SHA256
  480777d3b02f2f009a157b583390186886708d10632f9a178794e17f25455fb3.
- First AUDIT.json SHA256:
  cd88a3526da2e70045b8a0f09204a364c5a1845de57d98ab1c8c2d5e90e52e3e.

Construction8/8 and the original two-call minimal probe remain excluded. Setup
notes retain two local archive-inspection mistakes before source reconstruction;
no old study or blocked payload was rerun/republished. Prior batch-cost and
XDamage evidence remain unchanged. Other packed-index/reader allocations were
not modified. Intake searches were bounded/non-atomic, not proof about unpushed work.

## Environment and complete reproduction

Supplied Linux6.18.44/x86_64 execution container, CPython3.13.5 stdlib, binary64
float, guest AMD EPYC9V74, five CPUs, frequency unpinned. Docker/gh absent; no
Docker/OrbStack image-attestation or cross-platform replication claim. No install,
GUI/model/provider/user document/task input or experimental network call.

Six binary data parts plus CAPSULE.json restore all73 original files /189619
member bytes, including all raw outcomes, source, construction, source freeze
and audit receipts. Complete XZ16284 bytes SHA256
7816e953511798d1291706e011ae1f3ae79fa6e39e99d2a6c1e841f5f51d6b3a.
The capsule does not substitute generated traces for raw evidence. Readable
sources are also directly reviewable beside it. The restorer verifies identity,
bounded expansion and canonical paths before creating a new destination; it
executes no stored code. Use trusted/quiescent local paths, not a filesystem sandbox.

From this directory, Python3.13 standard library:

```sh
python -S -B verify.py
python -S -B -m unittest -v test_engineering test_unpack
# Optional data-only extraction; destination must not exist:
python -S -B unpack.py /tmp/reader-f17-retained
```

`verify.py` restores all73 files, compares the18 frozen members plus FREEZE with
readable publication, reruns only the raw auditor, requires byte-identical original
AUDIT output and checks all restored files remain unchanged. It supplies the
recorded interpreter path to the audit module's historical-argv expectation;
it does not alter the current interpreter or assert platform equivalence.
Direct `audit.py` replay assumes the original executable path, so the wrapper is
the portable historical-verification entry point. It launches no measured CLI.

Local fresh restoration passed, the audit output was byte-identical, and5/5
packaging tests rejected missing/changed/reordered parts or occupied destination.
These checks are not GitHub CI. Do not rerun the consumed run.py allocation to
repair or extend this record. Packaging helpers were added after the outcome and
are not falsely included in the pre-execution freeze.

## Integration disposition

This complete evidence bundle supports considering the limited parse_float change
at the experimental reader boundary. It does not itself modify the shared reader
or make this a production parser. Qualified PR review/checks and exact main
readback remain separate delivery gates. #3876/#57 and the global ROADMAP remain
open. Preserve this branch while its PR/dependencies exist; no foreign cleanup.

Primary references: Python3.13 json documentation (parse_float, parse_constant,
allow_nan), https://docs.python.org/3.13/library/json.html ; RFC8259 section6,
https://www.rfc-editor.org/rfc/rfc8259.html#section-6 .
