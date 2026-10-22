# Retained-result audit and crosswalk v2

The original `audit.py`, `analyze.py`, and `RESULT.json` remain unchanged. A mutation check showed that the original audit returned `AUDIT_PASS` after edits to a cover terminal status, acceptance timestamp, aggregate death count, and physical-occupancy limitation. The raw outputs are recorded in `LEGACY_AUDIT_MUTATION.json`.

The original crosswalk also folded `running_action_invalidation` into `policy_invalidation` with a fallback expression. Decision 3 consequently looked like a policy-monitor invalidation even though it was a running action-validity revocation. Its final returned-action admission was `INPUT_ADMITTED`; the already-admitted plan was then canceled, released with verified empty keys and buttons, and terminated with zero completed steps. Those are separate states in time and must remain separate in the diagnosis.

`analyze_v2.py` creates the additive `RESULT_V2.json` from the commit-pinned report and event stream. It refuses to overwrite an existing output and records policy-monitor invalidation and running-action invalidation in distinct fields. For a running action, it joins the exact plan ID to the accepted row, matched cancellation, input-release receipt, and terminal, while omitting the intent token. `RESULT.json` and the historical producer remain intact.

`audit_v2.py` checks the original saved result and independently reconstructs the complete v2 result from the frozen inputs. It validates source blob IDs, hashes, byte counts, exact JSON types, and all result keys/values. The tests reject mutations to score, scope, timestamps, invalidation separation, the canceled plan, verified release, and terminal step count.

Reproduce the saved-result audits and tests from the repository root:

```text
python3 -B research/doom/v39_retained_diagnosis_59_a01_20261005/audit.py
python3 -B research/doom/v39_retained_diagnosis_59_a01_20261005/audit_v2.py
python3 -B -m unittest research.doom.v39_retained_diagnosis_59_a01_20261005.test_audit_v2 research.doom.v39_retained_diagnosis_59_a01_20261005.test_diagnosis_v2 -v
```

To generate a separate copy for inspection, provide a new path to `analyze_v2.py`; it refuses to replace an existing file. This repairs the retained diagnosis association and result-field audit only. Threat descriptions remain model-authored; no per-action useful effect, causal survival benefit, matched recovery result, live threat response, or MAP01 exit is established.
