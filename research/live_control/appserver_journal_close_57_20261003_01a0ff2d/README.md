# Journal mutex retirement repair

`CodexAppServerClient.close(timeout)` previously reaped its child and joined the
reader, then waited without a timeout for the journal mutex. A different holder
could therefore keep this cleanup call blocked indefinitely. The local repair
uses the existing per-stage timeout for this mutex, raises `TimeoutError` without
closing or changing the journal on acquisition failure, and releases only its
own acquired lock after close or an exception. Explicit `timeout=None` keeps the
existing unlimited mode. Every other client method is byte-preserved.

This is a concrete #57/#59 caller-recovery repair following b04b witness
5966606760. It does not give the complete close call, arbitrary journal flush/close,
pipe/descendant cleanup or OS I/O a hard deadline. The original client still leaves
the native test pipe handles for the fixture driver to close; those ownership
endpoints are recorded separately. No real Codex server, model, game, GUI, input,
physical release, general timing/token/resource benefit or formal allocation ran.

Actual Windows11 build26200 / CPython3.12.10 ordinary results:

| Stage | Methods | Exit | Preserved interpretation |
| --- | ---: | ---: | --- |
| First RED | 5 | 1 | mutex defect plus LF/native-CRLF fixture assertion |
| Corrected RED, unchanged client | 5 | 1 | mutex defect only |
| First repaired normal / -O | 5 each | 0 / 0 | finite lock and journal-error custody |
| Additional None compatibility RED | 2 | 1 | intermediate repair rejects valid None; no child |
| Final normal / -O | 7 each | 0 / 0 | mutex custody plus preserved explicit None mode |

All seven command receipts retain actual argv/cwd/PID/UTC/exits/streams and executed
source/test snapshots. There were18 ordinary owned silent-child invocations across
the necessary repair phases, max1 live, not18 independent formal trials. Seventeen
distinct PID numbers were later absent; PID reuse is not an extra worker. Every
owned reader/caller/process and driver-owned pipe closes in the recorded endpoints.
Initial temporary journal bytes were not captured beyond booleans; no original
bytes are invented. Corrected and later records include exact retained journal
base64, with the actual flushed platform bytes as their unchanged-byte reference.

The separately expressed saved-only reader reconciles35 retained rows/7 commands
and rejects9 semantic copies without running/importing a client, producer or test.
It is same-author evidence, not a nonauthor approval. `PROJECTIONS.json` separates
public stream/path/format identities from private-original receipt hashes. Original
raw/source/first failures stay unchanged; all snapshot helpers end `.txt` and are
proof data, not default test-discovery inputs. The active regression module is
added once to the existing native protocol selection, preserving all other suites.
The complete native/hosted CI is not claimed.

Prospective exact-content review and then-current nonauthor combination/live
platform/identity/authority/cancellation checks still precede any single expected-old
history-preserving main update. This archive itself contains no dynamic approval,
apply certificate or self-referential new commit digest.
