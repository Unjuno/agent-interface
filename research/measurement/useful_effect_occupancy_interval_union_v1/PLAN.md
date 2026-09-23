# #1328 interval-union occupancy equivalence

H/T/D/C/U are frozen in Issue #1328.

Construction/pilot IDs are excluded from formal. Pilot batch index 99 was used only to size outer invocations and is not pooled.

Formal is one logical deterministic invocation split into immutable subjobs to stay below the outer execution ceiling:
- exhaustive block: 1 run;
- bounded old-set equivalence: 5 batches ×100,000 =500,000;
- nanosecond stress: 5 batches ×20,000 =100,000.

Each batch output path must be absent before its one run. No batch rerun/replacement/tuning. Aggregation occurs only after all11 outputs exist. The parent #988 candidate is retained byte-identically; only the replacement occupancy helper is under test.
