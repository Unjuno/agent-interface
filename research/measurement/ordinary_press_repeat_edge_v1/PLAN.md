# ORDINARY-PRESS-REPEAT-EDGE-DISCRIMINATOR-20260917-001
BASE=4b106a9b549fc3499d39ef2c7e3367d95a6c736c
PINNED_V10_GIT_BLOB=341b3c01649943ddaad5f28431a792c4889cc36e

H: exact current v10 caller-visible input_admission cannot distinguish FIRST_DOWN from REPEATED_DOWN under matched public inputs/timestamps, although only FIRST_DOWN begins a new hold.
T: pure standard-library extracted ordinary-down information-flow model; fixed controls and 100,000 matched randomized pairs; hidden pre-state differs but is excluded from public receipt.
D: PASS iff all valid matched pairs have distinct hidden new-hold witness, identical complete public receipts, one press+sync in both modeled paths, and negative controls fail closed.
C: fake backend isolates information flow only; real X11/app effects are unmeasured.
U: source contract pinned by exact Git blob; no X11/model/task input; construction only.
