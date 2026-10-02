# Actual whole-window primary usage

The usage window begins with the allocation/scaffold-publication tool call and
ends with the first independent post-terminal app-event/release read. It includes
primary control, driver authoring, both image views and inspections; prior product
implementation/contract tests/build and later accounting/publication are excluded.
Requested source context is gpt-6.1-sol / medium. Cached input and reasoning output
are subsets, not extra tokens. No billing or provider revision is attested.
This is not a matched comparison to earlier cases, an image-only token estimate,
or evidence of reduced cost. Context length and work boundaries differ.

{
  "input_tokens": 1182158,
  "cached_input_tokens": 1169280,
  "cache_write_input_tokens": 0,
  "output_tokens": 4578,
  "reasoning_output_tokens": 778,
  "total_tokens": 1186736,
  "uncached_input_tokens": 12878
}

Nine exact source responses / 27 original source rows. Selected own tool and
usage records are retained in actual-source-records.jsonl; no reasoning or other
conversation records are included. verify_retained_usage.py replays their source
hashes, call IDs and usage counters offline. verify_usage.py separately supports
replay from the original private source log.
