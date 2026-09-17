# ORDINARY-ADMISSION-OWNER-IDENTITY-DISCRIMINATOR-20260917-001
BASE=8888ce1b5642932c00c40668c557ff8341b93555
PINNED_V10_GIT_BLOB=341b3c01649943ddaad5f28431a792c4889cc36e

H: two distinct InputOwner lifetimes can emit identical ordinary keyboard input_admission receipts under matched public key/timing/deadline fields because owner_id is not in that receipt.
T: pure standard-library information-flow model; fixed controls plus 100,000 matched owner-A/owner-B pairs.
D: PASS iff hidden owner differs in every matched pair, complete public receipts remain identical, changed public inputs remain observable, malformed controls fail closed, and owner_id is absent.
C: caller may already possess owner identity out of band; this tests receipt sufficiency only.
U: no X11/model/task input; construction only.
