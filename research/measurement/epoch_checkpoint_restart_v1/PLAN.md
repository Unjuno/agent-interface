# EPOCH-CHECKPOINT-RESTART-DURABILITY-20260918-001
BASE=0b7e543c6dc3d40cc61d30fa1cc97c4642bf40dd
PARENT_CANDIDATE_GIT_BLOB=ead96e6bed3630c377cacee9a460b42f4be59291
PRIMARY_SEED=104920260918001
PRIMARY_CASES=20000

H: a transactionally committed FULL_SEMANTIC_CHECKPOINT preserves exact #1040 semantic state and accepted-resync idempotence across a fresh process reopen; a CURRENT_ONLY negative loses gap/epoch/overflow semantics.
T: SQLite rollback journal + synchronous FULL + explicit transaction. Writer builds 20k deterministic #1040-style states, stores full checkpoint + expected view + current-only negative, exits. Fresh reader restores and compares all states, checks replay and monotonic future append on a fixed subset. Fixed corruption/uncommitted controls before primary.
D: PASS iff exact full restore20k/20k, replay idempotent, future append/stale rejection correct, current-only negative discriminates every case, corruption/schema/uncommitted controls fail closed, authority false.
C: persistence encoding may omit hidden state such as accepted_resync even when view round-trips.
U: process restart on one SQLite/container host only; no power-loss/controller/distributed durability claim.
