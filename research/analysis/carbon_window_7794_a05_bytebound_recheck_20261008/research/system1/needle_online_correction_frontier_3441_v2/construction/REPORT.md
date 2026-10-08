# Construction-only result — Issue #4826

**Disposition: `CONSTRUCTION_SIGNAL_FAIL_ONLINE_CORRECTION_FORGETTING`; not formal evidence.** This single construction diagnostic used the three seeds registered in #4826, so they were consumed there and never reused for #4829's fresh-seed formal allocation.

| Seed | Untouched base A | Candidate A, step 0→32 | Candidate B, step 0→32 | First D crossing |
|---:|---:|---:|---:|---:|
| 67117 | 256/256 | 256/256 → 0/256 | 0/256 → 256/256 | step 29 |
| 67229 | 256/256 | 256/256 → 0/256 | 0/256 → 256/256 | step 30 |
| 67341 | 256/256 | 256/256 → 0/256 | 0/256 → 256/256 | step 30 |

Construction tests passed 3/3. The independent read-only auditor recomputed all 99 per-arrival A/B accuracy and cross-entropy points, base outputs and final logits with zero errors; nine scope/epoch controls and metric/logit corruption controls passed. Exact raw file: 628,723 bytes; SHA-256 `1d70cae8f9e73bd6fee0fa49e0e177ddc29a4cf4c77c0fabe3bea3469b859404`. It is retained in 32 ordered chunks; `PARTS.json` records each piece hash and expected blob ID.

The trainer ran once as a construction diagnostic in the pinned local CPU image. It was not a formal run: there was no formal freeze-volume handoff for this allocation and no confirmatory claim. The diagnostic strongly motivated #4829; its finding was confirmed only on the separate fresh seeds in that successor.

The published runner snapshot was reconstructed from the construction working copy committed on the fresh successor branch before the formal seed change. Its computation/text matches the study implementation, but the original pre-run source byte hash was not captured. Do not treat this retrospective publication as stronger byte-level provenance than the raw hash and independent audit support.

No Astra, GUI, external effects, provider calls or action authority.

