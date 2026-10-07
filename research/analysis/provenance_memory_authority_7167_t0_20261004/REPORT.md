# Issue #7167 T0 result: `PASS_METHOD_SCOPED`

## Result

The frozen candidate ran once and exited 0. The independent auditor ran once
afterward and exited 0. It reconstructed all 10 stored synthetic records, 3
application-content summaries, and 13 retrieved rows. The active intent view
contained only two source-bound user instructions, including the newest
revision for the conflicting `task:draft` key; the superseded revision,
application text, model hypothesis, derived summaries, and missing-source row
were not re-emitted as active user authority.

The independent auditor rejected all four frozen corruptions: promoting
application content, dropping summary provenance, resurrecting the old user
revision, and trusting a record whose source is missing. No audit errors.

## Interpretation and limits

This passes only the frozen deterministic transformation contract. It shows
that the tested data pipeline can retain descriptive records while preserving
their stipulated provenance/authority classes through storage, exact-duplicate
summary consolidation, and retrieval. The fixture assumes source authenticity
and correct origin labels. It does not test whether an LLM follows labels, a
real memory store can be poisoned, an application can spoof provenance, or
any live security boundary. A T1 model/prompt-injection study would require a
separate authorization and freeze; none is implied by this result.

Host-only standard-library Python was sufficient; no network, model, GUI,
container, or external data was used. Construction-stage failures are retained
in `CONSTRUCTION.md`, separate from the formal result.

## Artifacts

See `FREEZE.json`, `RUN.json`, `SHA256SUMS`, and `formal_01/` for the frozen
source identity, exact one-shot invocations, candidate output, independent
audit, and digests.
