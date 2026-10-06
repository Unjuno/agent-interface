# #6526 retained publication intervals — pre-result plan

Worker: `01a0ff35-50a9-7a31-9007-2caa36152d68`. Ordinary finite CPU analytical construction, not an A04 formal allocation. No old candidate/auditor, Tk, container, image, model, display or input invocation.

Fixed retained source: main `332da58a9b6b825c384a142dfb59d7ed2b8b774e`. Intake advanced to `a3e93e471f065214ed01b050683aaecbe0db3b4d`; Git comparison of the entire A02 and A03 source/data directories found no difference. We select immutable Git blobs, not mutable checkout files. Existing unrelated checkout line-ending differences are excluded from this change.

## H/T/D/C/U

**H (logical, not the original causal hypothesis):** the upper endpoint after successful replacement is insufficient to prove a deadline miss whenever the deadline is inside the recorded interval. The retained interval may instead certify a miss from its lower endpoint. We do not assume which of these cases occurs in the 180 retained trials.

**T:** freeze this plan before parsing the full180 raw trials; check finite possible-time fixtures; bind the retained input bytes and source; reconstruct all180 trial identities, publication intervals and nominal deadlines; compare the historical endpoint labels descriptively. Independent reconstruction imports neither the producer nor the original candidate/auditors. Preserve every attempted command, failure, exit and hash.

**D:** for exact integer monotonic readings L=action_ns, U=persisted_ns and D=start_ns+deadline_ms*1,000,000, require L<=U. The successful os.replace occurs after L and before U in the same process. Use the conservative closed interval [L,U]: U<=D => CERTIFIED_ON_TIME; L>D => CERTIFIED_LATE; otherwise => UNRESOLVED. Equality at D is on-time under the original numeric deadline cutoff; this does not establish physical clock resolution. An independently enumerated set of possible clock positions must agree for every finite fixture. Negative control: treating U>D alone as a definite miss must fail for a straddling interval. All six cells contain exactly30 rows. Report identified miss-count bounds [late,late+unresolved], with n=30; these are logical identification bounds, not confidence intervals. Any missing/duplicate ID, wrong payload/type, changed source/input, inverted interval or inconsistent record prevents a data result. No tolerance, effect threshold or p-value is introduced.

**C:** these are bounds for this action's namespace publication by replacement, conditional on the recorded source/clock chronology. They are not an exact filesystem linearization timestamp or fsync/power-loss durability. candidate.py creates an output directory with exist_ok=True and does not itself prove it was initially empty; do not infer first-ever effect presence or strengthen labels from absence snapshots. snapshot_ns is before exists/read, so a late positive snapshot does not establish deadline presence. No source-level guarantee rules out external writers. Preserve these assumptions and limitations explicitly rather than silently regrading the experiment.

**U:** original A01 STOP, original A02 H_FAIL_SCOPED artifact, A03 HOLD_AUDIT_TIMING and H_NOT_EVALUATED remain unchanged. No new formal effect result, no replay, no claim about observer overhead or actual environments. A disagreement changes only this descriptive publication analysis. If retained labels happen to match the historical endpoint count, report the stronger justification and the failure of the general point-timestamp rule, not a new positive discovery.

## Variables and custody

| Symbol | Definition | Unit / source |
|---|---|---|
| L | Reading before temporary write and replacement | integer ns, action_effect.action_ns |
| U | Reading after successful replacement | integer ns, action_effect.persisted_ns |
| D | Nominal deadline | integer ns, trial_start.start_ns and frozen deadline_ms |
| tau | Unobserved publication clock position | conservatively L<=tau<=U |
| S | Reading before snapshot exists/read | integer ns, deadline.snapshot_ns |

Use the A02 fixture/candidate/freeze, its frozen trial input, candidate receipt, complete event stream, audit artifact, all180 deadline/effect pairs and original SHA256SUMS as immutable inputs. Retain path/mode/Git blob/size/SHA256 for each selected file. Also pin A03 posthoc_audit.py and REPORT.md for the historical comparison; do not run them. Source path: `research/analysis/observation_intervention_6526_a02_orbstack_20261003/`; A03 sibling: `observation_intervention_6526_a03_deadline_audit_only_20261003/`.

Source reasoning uses Python3.12 documentation: [os.replace](https://docs.python.org/3.12/library/os.html#os.replace) describes successful atomic replacement on POSIX, and [monotonic_ns](https://docs.python.org/3.12/library/time.html#time.monotonic_ns) supplies monotonic integer readings. The interval inference comes from their ordering in the actual fixture. Nanosecond representation is not a measured resolution or scheduler guarantee.
