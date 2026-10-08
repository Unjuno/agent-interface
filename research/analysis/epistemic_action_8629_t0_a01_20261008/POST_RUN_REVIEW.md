# Post-run review — Issue #8629 T0 A01

The one-shot run is retained as `HOLD_CANDIDATE_ENTRYPOINT_NAMEERROR`; see [FORMAL_FAILURE.md](FORMAL_FAILURE.md) and the exact machine receipt/raw files in `formal/`. No candidate data or auditor result exists. The pre-freeze construction tests were insufficient: they exercised policy behavior but failed to launch the frozen candidate CLI as an integration path, allowing undefined names in `candidate.py` to pass.

The freeze package was committed before launch. During a pre-launch remote custody check, the GitHub base64 transport for `fixture.json` was found not byte-identical; no formal process had yet run. The original freeze commit was preserved, and a follow-on branch commit replaced only that fixture blob. Its Git blob SHA now matches the host file (`be3c43ae75fe2db37e2495d2e270a933953f0418`). The runner then verified its local frozen SHA-256 manifest before its sole execution. This transport correction is provenance context, not a protocol or result change.

Follow-up: create a separately allocated successor that adds a frozen candidate-CLI smoke test proving imports and a valid output schema, keeps raw-input custody explicit, and repeats the independent auditor validation. The successor must use a new seed/allocation or clearly state that it is an execution-repair replication; it must not replace or silently rerun this failure. Until then, Issue #8629's diagnostic hypothesis remains unevaluated.

Scope remains finite synthetic method research only; no model, agent, human, GUI, safety, or product claim.
