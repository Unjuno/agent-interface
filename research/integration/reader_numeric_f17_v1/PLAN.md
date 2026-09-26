# Engineering #4371: finite numeric response boundary

Allocation: reader-numeric-f17-20260925-01. Intake main:
4a1f3957e91b412a64769199f78f2c4b0102d28b.

## H / T / D / C / U

H: A decoded overflow must be rejected at record parsing, not at final response
serialization. Keeping the exact CLI and adding only a finite parse_float hook
should retain the good prefix and cursor in an exit-2 blocked response.

T: Sixteen short, fixed CASES.json streams; original and candidate reader copies;
one page32 call and a page1 plus saved-cursor page32 continuation. Exactly96
separate Python -S -B module CLI invocations. Policy order alternates by fixture.
No CLI call performs input or acknowledges anything. Every fixture/cursor,
argv/stdout/stderr/process exit and acquisition bracket is retained. Source and
corpus are published and read back before the one run. An out-of-range baseline
exit1 is an expected measured result, not an orchestration failure. A timeout or
failed first page stops the allocation without retry. Run process timeout25s;
individual CLI timeout5s. Construction is separately retained and excluded.

D: PASS_FINITE_READER_RESPONSE_ENGINEERING requires all96 records, exact frozen
sources and corpus, expected10 baseline overflow crashes with no stdout,10
candidate structured refusals with preserved prefix/cursor, full unchanged
responses in the other76 calls, unchanged stream/cursor bytes, neutral authority
flags and raw-only audit. Ten effective audit corruptions must reject normally.
A complete mismatch is FAIL; missing source/process/evidence or audit coverage
is HOLD/STOP. No same-ID reruns, replacement rows or post-result tuning.

C: This deliberately narrows numeric representation to finite Python floats.
The number1e400 is legal JSON syntax; the limitation is representability and
response encoding. Underflow, rounding and signed zero keep Python float
semantics. Decimal precision is not preserved. Literal NaN/Infinity, quoted
strings, duplicate keys and incomplete LF frames are different parser branches.
The fixture producer is trusted and file contents quiescent. No broad parser
soundness, hostile-input performance, extreme nesting or arbitrary cursor claim.

U: Supplied Linux container/CPython3.13.5 only; no pinned Docker/OrbStack image.
No GUI, model/provider, task input, package install or experiment network.
No token/latency/throughput, user-recovery or production promotion claim. The
independent auditor is separate code, written by the same author, not a human
review or second implementation of Python's JSON decoder. Logical counts and
hashes are exact; a calibrated uncertainty or coverage factor is not applicable.

## Proof of the proposed bounded change

The existing parser calls its float hook whenever a decimal or exponent-form
numeric token is decoded, including tokens nested in objects or arrays. The
candidate uses the same float conversion as before. If the result is finite,
it returns that exact float without rounding it again. If it is non-finite,
it raises ValueError inside the existing per-record try block. That block sets
blocked/INVALID_JSON_RECORD and exits the record loop before either append or
cursor increment. Thus previously admitted records are retained and the cursor
still names the offending line's start. No CLI change is needed: the response
now contains only previously accepted serializable values and is emitted with
exit2. This argument assumes ordinary finite-depth JSON, successful I/O and
no other serialization error; it is not total correctness for arbitrary input.

The independent auditor parses numbers as Decimal and compares their absolute
values to the exact binary64 round-to-nearest overflow boundary. It constructs
expected records/cursors without importing either reader or the runner. Finite
expected float payloads use the installed Python conversion; independent
arbitrary-precision-to-binary rounding is not claimed.

## Variable / field table and unit check

| Symbol or field | Meaning (Japanese) | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| value / number | JSON数値字句／変換後の値 | 1 (dimensionless) | bounded fixture string / Python float | string / scalar |
| offset | 消費済み接頭辞の長さ | 1, byte count (not SI base unit) | complete LF boundary within input | integer scalar |
| next_sequence | 次に期待するレコード番号 | 1 | count of consumed LF plus one | integer scalar |
| start_ns / end_ns | プロセス呼出しの観測時刻 | s, stored in ns | same monotonic clock, end not before start | integer scalar |
| records | 返却済みレコード列 | 1 | ordered complete accepted records | list |
| prefix_sha256 | 既読接頭辞の識別子 | not a physical quantity | SHA256 hex of exact prefix bytes | string |

Unit check: byte offsets are compared only with byte lengths; line counts only
with sequence counts; time endpoints share one clock and are not compared with
record counts. No timing threshold or performance inference is used.

## Sources

Python3.13 json documentation, parse_float/parse_constant/allow_nan:
https://docs.python.org/3.13/library/json.html
RFC8259 section6, representability and interoperability:
https://www.rfc-editor.org/rfc/rfc8259.html#section-6
Exact upstream Git reader ea72c166c2cea511ea91031dfbb14563fe4e3245 and CLI
1a97a659113666ccaa254ab2bf5dc0306e217015; both checked against local bytes.

## Roadmap / integration boundary

Intake -> excluded construction -> exact public source/corpus freeze -> one
retained matrix -> raw-only audit and effective controls -> full additive
research-evidence PR -> exact-head checks/review -> qualified main readback.
Only this namespace is owned. No existing reader/runtime/workflow or historical
result changes. Runtime adoption would need a separate shared-source decision;
#3876/#57 and the global ROADMAP remain open. Publication failures stay here.
