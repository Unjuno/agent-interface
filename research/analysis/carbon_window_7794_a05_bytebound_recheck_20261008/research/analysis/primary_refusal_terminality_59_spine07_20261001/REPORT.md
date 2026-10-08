# Result — #59 spine-07 malformed-envelope caller test

**FAIL_UNCERTAIN_DELIVERY_REPLAY.** The exact spine-07 candidate raised a TypeError when it read the first malformed reply. At that point caller state remained unstopped (`null`). After the primary-like caller caught that error, a second dispatch reached the mock host and returned a completion-shaped response. Only after that second response did the caller latch `incomplete input or unverified neutral release`, too late to prevent the replay.

One Node process, two caller attempts, one test sequence. The independent raw-only audit checks the exact candidate blob identity and the retained output fields. There was no rerun.

This does not establish a live transport failure or any GUI/input effect. It is a construction FAIL in the primary-policy composition at the current #5639 head. The prior spine-05 and #5685 allocations remain unchanged. A successor should move envelope parsing/validation inside the caller's fail-and-latch boundary and retain a regression asserting zero second host dispatches after malformed replies; only a newly frozen source may be tested.

The tested file blob was re-read from the currently advanced #5639 head after the run and remains byte-identical; the failure therefore still applies to the current candidate source. Evidence delivery uses a fresh branch based on the latest main observed at packaging, not the experiment's earlier main.

Audit setup history: the first auditor invocation stopped with `FileNotFoundError` because the already-fetched frozen candidate had not yet been copied into the additive evidence directory. No candidate was rerun. The exact source bytes were copied, source identity verified, and the subsequent raw-only audit passed. The initial audit setup STOP is retained here rather than relabelled as a candidate result.
