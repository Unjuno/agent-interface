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

Combined reply-ID/journal/reader/EOF tests pass 16/16. Complete native contract
runner and analysis-index CI results remain pending; this is not merge-ready
or proof of genuine provider, GUI, native input or formal scientific execution.
Red/green and combined logs remain beside this note.
