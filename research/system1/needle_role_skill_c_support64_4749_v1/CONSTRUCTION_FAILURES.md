# Construction and preflight failure chronology

- First Windows host unittest: 7/9 passed; two tests used Docker-only /raw fixtures and failed on Windows path semantics. No formal training occurred.
- First Linux container unittest: same two fixture failures because /raw was not mounted for that invocation. No formal training occurred.
- Tests were changed to resolve retained construction fixtures relative to the test file. A full offline Docker rerun passed 9/9, including independent deterministic retraining.
- Initial Docker inspect template referenced a field absent from the Ollama container metadata. Corrected inspection succeeded; no container state changed.

No event above touched or consumed a formal seed. No formal outcome was retried or relabeled.
