# Actual combined primary usage

Six exact source responses / 18 original selected own source records are retained.
The window begins with allocation/scaffold publication/launch and ends with the
first independent post-terminal app/release read (including the initial issue
state read). It includes driver authoring and combined send/read/image turns.
Prior implementation/contract tests and later auditing/accounting/publication are
excluded. Requested source context is gpt-6.1-sol / medium; provider revision and
dollar billing are not attested. Cached input and reasoning output are subsets.
This is not a matched comparison to earlier windows, an image-only estimate or
evidence of cost/token reduction. In particular, fewer selected model responses
do not by themselves imply lower total input usage: context/work boundaries differ.

{
  "input_tokens": 1293967,
  "cached_input_tokens": 1283584,
  "cache_write_input_tokens": 0,
  "output_tokens": 7752,
  "reasoning_output_tokens": 4426,
  "total_tokens": 1301719,
  "uncached_input_tokens": 10383
}

actual-source-records.jsonl contains exact original tool/usage rows and hashes,
no reasoning or other chats. verify_retained_usage.py replays the original hashes,
call IDs and counters without the private full session log. Original full receipt,
raw stream and selected observer projection are distinct artifacts.
