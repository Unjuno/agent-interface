# Corrective audit supplement for PR #7675

The original `audit.py` / `AUDIT.json` remain unchanged as the first audit attempt. Review of the PR head found that v1 keyed expected states from case labels, did not validate all candidate fields before mutation controls, and hard-coded the same-final/distinct-history claim. Its PASS receipt is therefore not sufficient evidence by itself.

`audit_v2.py` independently derives dispositions from raw event sequences, validates the exact shared terminal visual state and distinct raw histories, joins all output rows by unique case ID, checks every output field against the source events, and rejects eight isolated raw/result mutations. It reads the original `INPUT.json` and `CANDIDATE.json`; it does not import or rerun `candidate.py`. This is a new audit version of the same retained finite fixture, not a replay of the candidate allocation. The old audit result and hashes are preserved.

The final scoped disposition is supported only if this v2 audit passes. It remains synthetic method evidence, with no live task or benefit inference.
