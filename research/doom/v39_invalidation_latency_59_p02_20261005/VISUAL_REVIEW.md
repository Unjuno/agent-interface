# Visual review of frozen threat frames

I opened the exact Git-tracked full-observation PNGs pinned in `FREEZE.json`. Sequence 166 shows the corridor with no hostile in the visible viewport. Sequence 200 shows a hostile in the lower corridor. The hostile remains visible in sequences 217 and 218; in sequence 218 it is directly ahead while the HUD reads health 48 and ammo 37.

The event log has a typed row and a paired full `observation` row for every listed sequence. Each pair has `exact=true` and the same RGB frame hash. The PNG blob and event rows are pinned by Git blob ID and SHA-256. The typed row’s `artifact_published=false` flag means the typed event did not publish a separate image artifact; it does not mean the paired full observation image is absent.

This is one analyst’s visual classification, not an independent second review or a machine enemy detector. “No hostile visible” applies only to the pixels in sequence 166; it does not imply no off-screen enemy. The first retained visible hostile in the sampled set is sequence 200, during the pending model interval; exact onset between samples is unknown. The visual sequence does not establish that the hostile caused the health decrease.
