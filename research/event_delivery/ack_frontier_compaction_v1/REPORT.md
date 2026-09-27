# Complete-ACK frontier composition — retained counterexamples with formal HOLD

Issue #4026. Parents #916/#926; #3986 was already integrated by PR #4004 and was not rerun. Read [PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U, conditional induction argument and complete variable/unit table. This directory is additive research evidence, not production runtime.

## Disposition

**Execution: STOP_SUPERVISOR_TIMEOUT. Formal scientific result: HOLD_FORMAL_INCOMPLETE.**

The one publicly hash-frozen48-case allocation reached its registered30-second outer subprocess timeout. Forty cases have complete records, the next case has three retained operation receipts, and seven later cases were not started. The48-case formal denominator is not satisfied. The unchanged formal auditor exits1 at `case denominator`; it was not modified to accept fewer rows. No rerun, replacement, pooled construction row or post-freeze source/gate change occurred. Unknown supervisor returncode and absent END.json remain unknown/absent.

The separate posthoc prefix characterization reconciles all40 complete cases and188 actual operation-process exit receipts. It reuses only the frozen independent list-state oracle, not tested SQL model/runner modules. It does NOT return a formal PASS or establish the full preregistered result. Its12 copied-evidence controls reject; a separate changed-source control also rejects. All13 frozen source hashes remain exact. Same-author separate implementation/process is not independent human review.

## Observed finite prefix

Counts below are from the exact retained schedule prefix, **not balanced rates or reliability estimates**.

| Observed count | Retained-rows-only | Persistent ACK frontier only | Frontier plus bounded ACK |
|---|---:|---:|---:|
| Complete cases |13|13|14|
| Genuine next-event attempts blocked after full ACK |5|0|0|
| Acknowledged old-event readmissions |2|0|0|
| ACK advanced beyond accepted history |1|1|0|
| Event admission skipping an unaccepted predecessor |0|1|0|

1. **Compaction counterexample.** With E1..E3 initially accepted, ACK3 legitimately removes every consumer row. Retained-only MAX becomes0. It refuses genuine E4 and can readmit E1. The independently observed database transitions and actual worker responses are retained in `formal-01/rows.jsonl`; e.g. `r0-FULL-legacy` and `r0-OLD_REPLAY-legacy`.
2. **Untested-trust shortcut counterexample.** Taking MAX(retained rows, ACK last_seq) fixes valid compaction but trusts the inherited ACK procedure. After ACK2, a claimed ACK4 hashes the same retained E3 row as ACK3, advances last_seq to4 despite E4 never being accepted, and admits E5. `r0-FUTURE_ACK-frontier` retains this exact sequence. The digest does not by itself prove the claimed ACK position was accepted.
3. **Bounded candidate observations.** The additive ACK upper-bound guard rejects that future position, and its retained complete cases preserve the expected valid/gap/replay/digest behavior. This is not an overall formal PASS: the second repetition is incomplete.

These are actual isolated SQLite application-model observations. They are not findings about an external service, a SQLite defect, the current passive reader's implemented ACK semantics, or a production safety certification.

## Partial case: missing response is not an absent database update

`r1-ACK_REPLAY-frontier/partial.json` contains initialization, ACK3 and exact ACK3 replay. Its last recorded state has no pending event. The retained final database independently contains pending E4. Therefore the final database is not fully accounted for by the three retained receipts. The planned next operation was offer4, but its response/exit was not retained; we do not invent one or mark the case complete. The final DB bytes and last recorded snapshots remain available. This is an unplanned descriptive observation, not an additional registered study or automatic replay authorization.

## Construction, execution and provenance

Excluded construction completed24/24 cases with114 distinct operation processes, four offline test methods and12 rejecting semantic/provenance mutations. Those data are not in the formal denominator. The actual construction receipt and complete data are retained.

Preformal public freeze: commit33db0821e1a9780f4f88eec1e47b2b07f89b1f70; Issue comment5767293227. FREEZE.json SHA256 `7d4f85234b7b63fa41fc3fdac677685312ad4bb5a1f823012906f476b007fa67`; remote Git blob `ab83448a153dfe931c09d629bdb40501ce59fb86` matched local bytes before execution. Full source bytes were local and hash-bound at freeze; they are published with this evidence, not falsely described as uploaded before measurement.

Original #742 Git blob `1f4f83eb51e1af3fc915ace83f0a3a4da6dbd0a6` was retrieved via GitHub MCP. The exact #916 one-line contiguous reconstruction SHA256 is `7dbe43bc27ccc0d6f19b33c01e438aecd68c33753c512963d8697a426c5d35c6`, byte-identical to the previously retained archive. `CHANGES.diff` shows the two additive modifications; shared runtime and all old evidence remain unchanged.

Actual environment: provided Linux6.18.44 x86_64 container, CPython3.13.5, SQLite3.46.1, DELETE journal/FULL synchronous setting, BEGIN IMMEDIATE per mutation. Each operation used a fresh exec'd process and database connection. The parent observed tables independently using a read-only connection. Docker CLI/image identity unavailable; no Docker/OrbStack replication. No package install, GUI/input, model/provider, experiment network or credentials. Worker environment contains only PATH and LANG. Timing is diagnostic, not benchmark evidence; no calibrated uncertainty or hard deadline is claimed.

After timeout, an exact-script /proc check found no remaining owned runner/worker. That later absence does not recover an unobserved earlier exit. No physical input had been requested by this study.

## Integration consequence and limits

Before combining ACK-driven retention removal with contiguous admission, sequence progress cannot depend only on rows that compaction deletes. A persistent frontier helps only when its advancement is constrained by accepted history. These are concrete constraints on a future #3876 composition, not a new queue implementation or runtime promotion.

No automatic deletion of refused old pending heads, general pending-position stability, cross-session epochs, authentication, recoverable payloads, real producer/host integration, model consumption, power loss or distributed exactly-once claim. The conditional proof in the preregistration addresses admission/ACK frontier preservation only. #3876/#57/#2789 and ROADMAP stay open. The execution incident is kept here rather than creating a wrapper-successor Issue or repeating science until its wrapper passes.

## Read-only reproduction

After restoring the complete bundle to a fresh directory:

```sh
python -I -S -B test_contract.py -v
python -I -S -B audit_prefix.py formal-01 > /tmp/ack4026-prefix.json
cmp PREFIX_AUDIT.json /tmp/ack4026-prefix.json
python -I -S -B audit.py formal-01 --controls
```

The last command is **expected to exit1** at the incomplete48-case denominator. It must not be presented as successful formal validation. Do not rerun the consumed formal runner. All original absolute command paths in raw receipts identify the execution location, not paths to be executed on a reviewer host.

## ERROR CHECK

Source13/13 unchanged; no old result edits; full formal audit fails as required; prefix40/40 reconstructs; construction excluded; unknown terminal preserved; posthoc controls cannot upgrade the formal HOLD. No statistical, model/task or product benefit is inferred.
