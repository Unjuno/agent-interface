# Boolean response ID rescue

Source: `03a7d3090a20b3aa84bf35a57336700b26cf6ce1`.
All 94 packet files restored with exact Git bytes (root staged comparison exit0).
Original Windows comparison and failures remain historical and unchanged.

Fresh macOS test-first check on current main demonstrates Boolean true payload
returned for numeric request: one of two public stdio tests fails. Two-line
Boolean exclusion fixes this: both normal and optimized pass 2/2. Integer and
float numeric replies remain supported; Boolean frames remain journaled but
are not cached. Current stderr/reader/journal retirement logic is not replaced
with the older source. Shared protocol suite gains only the reply-ID module;
all existing registration is retained.

Combined reply-ID/journal/reader/EOF tests pass 16/16. Local analysis-index CI
completes 43 steps with no failures. Full native runner is FAIL: candidate
protocol435 tests,5 errors/5 skips; harness205 tests,31 errors. Exact parent
c45eb3631 baseline also FAIL: protocol433 tests,5 errors/5 skips and harness205
tests,31 errors. Error test rosters compare equal. All36 errors trace to Linux
`/proc/self/ns/pid` access through current_owner_identity on macOS. Tests are
not suppressed and no substitute process identity is introduced.
Existing Docker image inspection fails with daemon blob operation not supported;
no container launched/reset/pruned/pulled. Linux hosted validation is still needed.
Full native baseline/candidate outputs remain in local outputs/replyid-native*
logs; transfer to this packet remains pending because the first read was truncated.
Red/green and combined logs remain here. This is not a whole-suite PASS, merge-ready
delivery or genuine-provider/GUI/native-input/formal scientific execution evidence.
