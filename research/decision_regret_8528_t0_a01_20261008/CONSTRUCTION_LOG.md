# Construction log — Issue #8528 T0 A01

Construction is separate from the formal run ledger. No formal candidate or formal audit invocation has been made.

1. Authored `test_candidate.py` and `test_audit.py` before implementation; initial red run failed on missing modules as expected (one construction suite invocation; formal count unchanged).
2. Added finite visible/truth fixtures and candidate implementation. Candidate tests: 3/3 passed.
3. First independent-auditor test attempt exposed recursive mutation probes. Fixed probes to invoke the audit without recursively running probes.
4. Subsequent test run exposed an incorrect expected age for incomparable clock (`[0]` instead of `[null]`) and a fixture tick-index error; both were corrected.
5. A mutation test was accidentally regenerating the candidate after mutating an input, making it a valid new packet rather than a corruption. Changed it to hold candidate bytes fixed against altered input, so the auditor must reject the mismatch.
6. Candidate suite: 3/3 passed. The mutation-fixture no-op was traced to changing a tick whose action set was already `A`; moved the corruption to a tick whose frozen set is `A/B`.
7. A full Issue #8528 requirement reread identified that the initial audit report did not emit explicit age-only and unsafe-exposure comparator cards and used an implicit rather than supplied toy loss table. Added both comparator cards, a frozen finite loss table, and two additional corruption probes for loss and causal lineage. These are still construction-time additions; all formal counts remain zero.
8. Primary comparator cards tie at age-only sum 12 / toy unsafe exposure 0; the no-opportunity comparator is null. Latest suites: candidate 3/3 passed, independent audit 8/8 passed, and all seven mutation probes were rejected. Formal counts remain 0/1 candidate and 0/1 auditor.
9. GitHub readback of the first source freeze found stale protocol wording that still said five mutation probes. No formal command had run. Added an additive pre-formal protocol correction preserving the original freeze in history, corrected the count to seven, made the primary comparator tie explicit in H, and added an amendment record. Re-run both construction suites before corrected-freeze publication.

The construction failures were harness/auditor implementation defects, not formal scientific outcomes. They remain visible here rather than being represented as successful formal trials.
