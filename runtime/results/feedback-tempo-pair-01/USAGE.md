# Actual primary usage and strict attribution boundary

Eight unique primary responses in one combined chronological window:
- input_tokens: 1,367,369
- cached_input_tokens: 1,356,288 (subset of input)
- uncached_input_tokens: 11,081
- cache_write_input_tokens: 0
- output_tokens: 4,027
- reasoning_output_tokens: 285 (subset of output)
- total_tokens: 1,371,396 (= input + output)

These are actual recorded counters, not text-byte estimates or invented per-tool
costs. The selected boundary starts with the tool containing source scaffold
commit/build and first baseline allocation, then includes both live arms' control,
original image presentation and primary review work. The end tool includes
candidate close, terminal wait and first independent application-event read.
Later artifact audit, same-frame re-view/correction, accounting and publication
are excluded. Prior route/configuration inspection is excluded.

Baseline close and candidate allocation share one tool boundary; responses cannot
be assigned exclusively to independent arms from this window. No per-reply/task
cost, compression gain, cold-start denominator or billed-money comparison follows.
The large cached-input sum includes reused prior conversation context. Cached
counts are not free tokens, and billed amounts/prices are unavailable here.
No sum of reasoning/output or cached/input is valid because those overlap.

Recorded requested context: gpt-6.1-sol, medium effort, same active primary turn.
This is not a provider revision/fingerprint attestation. No subagent or new model
was launched. Source is only this primary caller's own session log. Projection
retains exact tool boundary IDs, source line numbers/digests and response IDs.
An independent source replay matched 24 source records, deduplicated all eight
response IDs, checked original counters and recomputed totals. It does not rerun
any live case or alter the earlier artifact audit. Raw session contents are not
copied into the report. Billing remains null; performance disposition stays HOLD.
