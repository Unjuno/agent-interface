# Bounded-skew contextual join successor (#2012)

Decision: PASS_BOUNDED_SKEW_CONTEXT_JOIN_SCOPED

H/T/D:
- Directed finite fixture over authority/target/effect critical fields and screenshot/focus/status_text contextual fields.
- Exact coherent, bounded skew, excessive skew, critical mismatch, session mismatch, surface mismatch, stale critical, missing, duplicate, and equal-timestamp controls: 10/10.
- Results: COHERENT=3, SKEWED_CONTEXT=1, STALE=2, UNJOINABLE=4.
- The only bounded-skew result contains contextual evidence; critical mismatch never becomes COHERENT.
- Every result carries grants_input_authority=false.
- Corruption control changing contextual evidence to a critical role fails closed.
- formal=1, audit=1, reruns=0, tuning=0.
- SHA-256: 81ac4c8679c42d4d37e0b14c0c38bfd4dd923ee237e88461777972e0d8d80068.

C/U:
This is a directed finite semantic fixture, not a runtime benchmark. It does not establish actual usefulness, latency, token savings, clock comparability, model quality, GUI correctness, or production transfer. The bounded-skew threshold and field-role declarations are explicit policy inputs. Stop after this result; a later successor must use a live observation fixture before promotion.

Additive path only: research/analysis/bounded_skew_context_join_successor_1218_v1/**
