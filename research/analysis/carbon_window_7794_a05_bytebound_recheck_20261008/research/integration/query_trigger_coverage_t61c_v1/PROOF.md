# Conditional argument and counterexample

Symbols and units are defined in PLAN.md. This is a fixed-query application argument, not a general SQL correctness proof.

1. Preparation acquires Q_p, e_p, c_p and T_p in one read transaction. The definition-checking policies require T_p to equal the known correct initial trigger contract; no preparation token is produced otherwise.
2. Suppose the database identity is unchanged, only ordinary DDL can alter the persistent trigger set, and the schema counter cannot be reset or wrap. Every committed DDL change increments c. Consequently c_v=c_p implies that no committed schema change occurred between those observations. A rolled-back DDL transaction also rolls back its data writes and is not a counterexample.
3. The initial INSERT trigger increases e for each committed inserted member of tenant A. In this study only one inserted row can change Q; no uninstrumented native writer or counter reset is allowed. With unchanged trigger coverage, e_v=e_p therefore excludes a committed result-changing insertion between preparation and validation. Thus Q_v=Q_p.
4. Validation runs inside BEGIN IMMEDIATE. All other writers and schema mutations are excluded until the private effect row containing Q_p commits. Therefore the equality from step3 still holds at that commit. This proves the scoped SCHEMA_COOKIE sufficiency, not safety of an external nontransactional action.
5. Trigger SQL equality at two endpoints does not imply step2: start with empty Q and e0; DROP the insertion trigger, INSERT one matching row, then CREATE the exact old SQL in the same committed migration. Q changes, e stays0, and both endpoint trigger sets are equal. CURRENT_DDL stores the stale empty result; this is a deterministic application counterexample to that weaker interpretation.
6. Conservatism: unrelated CREATE TABLE and drop/recreate without a data write change c but not Q. SCHEMA_COOKIE refuses these two conditions although result equality holds. It is sufficient under assumptions, not a necessary or availability-optimal predicate.

Dimension check: Q, e, c and T comparisons have unit1. No comparison involves elapsed seconds or system-clock synchronization. The numeric example is e0->e0 and c0->c0+2 with Q empty->[(1,9,1)].

ERROR CHECK: coverage, initial trust, same database, no-reset/no-wrap and atomic local effect are explicit premises. We do not prove trigger correctness from its text, general SQL dependency completeness, source authenticity or currentness beyond the transaction. SQLite documents schema_version as an internal/test-related mechanism; no production recommendation follows.

Primary specifications: https://www.sqlite.org/pragma.html#pragma_schema_version ; https://www.sqlite.org/lang_createtrigger.html ; https://www.sqlite.org/lang_transaction.html . Consulted 2026-09-26 JST; installed SQLite3.46.1 is recorded separately.
