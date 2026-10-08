# Post-merge evidence closure correction

The original PR #3636 was merged as `0c5efde47bb70a19e359853ac72da71265598515`. A read-back audit found that the 96-entry `evidence/RAW-MANIFEST.json` included eight `fixture.log` / `xvfb.log` files that were present locally and matched their recorded hashes, but `.gitignore` had prevented them from entering the main tree. The other 88 manifest entries were already present and hash-correct.

This additive follow-up adds those eight exact byte streams without changing any experiment output, report, manifest entry, allocation, or predecessor evidence. The files are 48-byte fixture logs (SHA-256 `e0a46db3e7d086b6ed55477f9c8cc5ec4dbe4b6ef804e1372e9a4a6dc5a6b01a`) and 2,348-byte Xvfb logs (SHA-256 `b987a262609a3720f450ab6815ed90b2069dd47b7b012959ca19c325aebf5d55`), one pair each for construction and formal-01/02/03. Repeated hashes reflect identical short process-startup/termination output, not duplicated allocation rows.

The correction is complete only after the PR merge and a fresh main-tree replay of every manifest path. This does not alter the scoped experiment decision or claim host/model-visible delivery.
