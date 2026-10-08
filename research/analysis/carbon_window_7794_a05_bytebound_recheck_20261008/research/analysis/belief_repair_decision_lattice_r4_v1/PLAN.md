# #1886 Belief repair decision lattice R4

H: retain ACTION_SAFE while a commit-recorded path remains current. Once stale, LOCAL_COMPLETE TRUE -> fresh-epoch local recommit, LOCAL FALSE -> reject; OPAQUE exact fingerprint + valid approval -> fresh-epoch recommit reusing approval, otherwise YIELD. Recommit never reuses old epoch.
T: exact Boolean product over path currentness, validator kind, local predicate, semantic fingerprint identity, approval validity and old epoch {1,2}; independent oracle; four negative comparators.
D: mismatch0; stale KEEP0; local recommit/reject both>0; opaque recommit/yield both>0; recommit epochs strictly newer; sticky/current-truth unsafe>0; always-yield false yields>0; old-epoch comparator violations>0; formal1/reruns0.
C: assumes trusted justification currentness and correct validator typing; no economics or fresh semantic-approval return protocol.
U: analytical composition only; no runtime/model/task/token/latency/GUI/product claim.
