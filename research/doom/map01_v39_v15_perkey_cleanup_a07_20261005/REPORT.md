# A07 result — STOP before input

Frozen candidate `22f869cc38b85611fe5de3ee4e4884b35d6fc61c9c227d28a37972624ca9cfa9` ran once under bundled host Python 3.12.14. Both arms terminated `failed` before step completion with `ValueError(\'observed input focus required\')`; no `input_release_transition` rows were emitted. The independent auditor returned `FAIL_RAW_OR_SOURCE_AUDIT` (20/32 checks).

Disposition: **STOP** under the preregistered rule because setup prevented both arms from completing. The fake server ended neutral during terminal cleanup, but no KeyPress/KeyRelease was tested. This is not evidence for retry behavior. The missing fixture contract was identified after the run: ExecutorV13 installs its own lease, and the fake action-loop boundary did not populate `expected_focus`. Preserve the candidate and raw/audit files unchanged.
