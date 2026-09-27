# Construction chronology

- First zero-training Docker preflight stopped at exact runner Git-blob verification because the local materialization had one extra terminal blank line (`ae980927...`, expected `ecd3a041...`). No training/model updates occurred.
- Removed the extra terminal blank line; local Git blob now equals the public main runner `ecd3a0414178f38535406573314793a40b353878` exactly.
- Offline pinned Docker construction then passed seed/image-independent checks: sentinel bytes round-trip, exact 64→16 prefix by shape/dtype/value/bytes, corrupted-prefix rejection, and AST parse of all executable sources. `CONSTRUCTION_PASS`; optimizer updates 0.
- Initial candidate seed 7866301 / v3 branch was abandoned before source upload or any run when a concurrent exact branch appeared. The branch is untouched. Seed 7866401 / v4 passed the collision searches and is the sole allocation in this study.

