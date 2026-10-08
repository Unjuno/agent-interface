# V19 per-actuation release-order map A02

## H / T / D / C / U

**H.** Replacing V19's single `state["admission"]` slot with a map keyed by the complete typed actuation identity can recover the admission corresponding to the final release for every admission/release ordering of 1–3 simultaneously held unique keys, while preserving exact identity and empty-held checks.

**T.** Pin the exact `_capture_backend` source from open draft PR #7692 head `7ec4e3ef405919bf5f1bfd9eeddbe630f3a5b32e`. Run a synthetic candidate wrapper over every admission-order × release-order permutation for N=1,2,3 (41 schedules); run malformed-field, bool/int alias, duplicate admission, and mismatched release controls; independently enumerate and audit the results.

**D.** `PASS_CANDIDATE` only if all 41 schedules produce an exact matching final DOWN/UP pair with an empty held set, and all identity/event mutations are rejected. A measured tail must remain censored on missing, duplicate, or mismatched identities.

**C.** The release contract may intentionally sample only the last physical release, or real runtime scheduling may never produce overlapping holds. Under either condition, full per-key history could be unnecessary for the current scorer-tail purpose.

**U.** The candidate is an isolated synthetic wrapper prototype. It does not execute V19's real backend class, scorer tail, controller, GUI, OS input, model, or game. It says nothing about how often overlapping keys occur, physical release correctness, task feedback, or efficacy. The source under test is an unmerged PR branch, not current-main runtime code.

## Result

`PASS_CANDIDATE`: all 41 schedules matched (1/1, 4/4, 36/36) with an empty final held set. The prior single-slot capture matched 15/41 (1/1, 2/4, 12/36). The map uses the typed tuple `(id, step, owner_id, intent_token, key, actuation_id)`. A duplicate admission marks the capture ambiguous and censors the candidate; missing identity fields, bool-for-int, and release mismatches also fail closed.

This is a construction result for optional scorer-tail pairing only. It supports a focused implementation/test follow-up to PR #7692; it does not establish measurement validity or runtime benefit. No source implementation was changed by this package.

## Reproduction

With Python 3.10+:

```powershell
python run_candidate.py
python verify.py
python -m py_compile run_candidate.py verify.py
```

`result.json` contains each schedule. `verify.py` independently checks the pinned source hash, complete permutation sets, final-pair identity, empty held state, and mutation outcomes.
