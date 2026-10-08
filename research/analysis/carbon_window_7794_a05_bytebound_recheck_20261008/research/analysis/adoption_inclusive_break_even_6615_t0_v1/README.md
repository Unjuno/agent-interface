# Issue #6615 — adoption-inclusive verified-work curve

This additive package is for a synthetic T0 accounting-method experiment only.
It compares setup-inclusive and prepared-only cumulative wall/human cost through
N independently verified useful tasks. It does not measure real installation,
operator burden, adoption, user preference, GUI behavior, or product value.

See PROTOCOL.md for the frozen H/T/D/C/U and decision boundary. The six
authored cases cover zero setup delta, setup-dominated short horizon, learning
with one failed attempt, setup failure, version-change repair, and unsupported
host work. Candidate and auditor are separate scripts; the auditor reconstructs
the raw ledger and costs without importing the candidate.

The unittest module is construction/mutation coverage, not the formal T0 run.
Formal candidate and audit invocations remain zero until the exact WSLc host,
cached image and CPU-only allocation gate are confirmed. Do not substitute the
shared OrbStack/Docker daemon.
