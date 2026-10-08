# MAP01 v12 physical occupancy R1 — independent replication audit

Run: `35443575048`  
Head: `01be2100203c3aac0b7104536a4d3a28e78fb0fe`  
Artifact: `10585310389`

Disposition: `PASS_MAP01_V12_PHYSICAL_OCCUPANCY_R1_SCOPED_REPLICATION`

The fresh PR-triggered container passed the import boundary and frozen preflight. Construction ran exactly once and passed. Formal ran exactly once after construction PASS; three fresh sessions passed with six actuation edges total. Maximum censor width was 0.666226 ms, below the 5 ms precision limit. Each session reported confirmed down/up edges, empty ownership after release, post-sample-up, terminal completion, and no errors. Reruns, replacements, tuning, authority expansions, and v3 physical promotions were zero.

This is a replication of the scoped R1 contract only. It does not establish a broad production, user-facing, or non-DOOM claim. The original run and its artifact remain immutable.
