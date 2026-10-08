# Late requests after negative outcome lookup — #4069

**PASS_LATE_REQUEST_IDENTITY_BOUNDARY_SCOPED. Research evidence only.**

A truthful NOT_FOUND response can precede the arrival of an original request. In32 frozen isolated process cases, per-attempt deduplication allowed4 late-arrival duplicate effects and2 altered-payload second effects. Stable intent plus exact parameters produced one effect in every case, rejected altered parameters, and retained typed refusals. The query itself was identical/read-only in both arms. This does not authorize generic GUI retries or establish distributed exactly-once delivery.

Read REPORT.md for the complete H/T/D/C/U interpretation, counts, limits and provenance. app.py is directly reviewable; the data capsule contains ALL new source, plan, raw requests/replies, native databases, relay/server journals, process exits, construction, freeze and audits. No experiment rerun is needed for review.

## Data-only restoration and re-audit

```sh
python -S -B unpack.py /tmp/late-status-4069-review
cd /tmp/late-status-4069-review
python -S -B audit.py --batches formal-00 formal-01 --reps 0 1 --freeze FREEZE.json --controls
python -S -B test_receiver.py
```

Use a new destination. Do not rerun consumed supervise.py/run.py formal batches. The frozen auditor's output must match AUDIT.json byte-for-byte. Re-audit runs no application/relay/model/GUI process. SQLite inspection is read-only on disposable copies. Unpacking verifies every part and member and executes no archived source.

Preformal public hash freeze:4eac33b35bd66aee294fc8061df9c71b3af68470. Full source/raw publication follows formal execution and is not claimed earlier. All32 app and32 relay exits and both batch exits are retained; audit is a separate implementation/process by the same author, not external review. No whole-repository local test PASS is asserted. Current-head CI/review/main readback are separate gates.

Only this additive namespace is changed. Original42/45-case conversation archives are NOT included in full here: only their unchanged-output re-audit receipts are included, explicitly marked in PRIOR_REAUDIT.json. Their historical publication debt and blocked notes remain preserved rather than being relabelled as complete delivery.

Supplied Linux x86_64 / Python3.13.5 / SQLite3.46.1, no Docker/OrbStack image identity; no install, external-network experiment, model/provider, OS/GUI input, production runtime mutation, performance/token or product claim. Parent #24's historical result, #3991, #4027, #2789 and the global ROADMAP are not closed by this result.
