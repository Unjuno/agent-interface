# Post-run audit addendum: read-only chronology validation (V3)

This addendum preserves the frozen A02/V2 package and adds a separately versioned read-only auditor. The original V2 source, test module, `FREEZE.json`, `RUNS.json`, A02 results and source archive remain unchanged.

V2's existing tests covered general raw tampering, but not a coherent classification-label swap. On a disposable archive clone, the new regression swaps one paired and one incomplete classification for each of baseline and candidate, updates status and projected outputs consistently, preserves the 15/85 aggregate, and updates the clone's manifest. V2 returned `PASS_READ_ONLY_ARCHIVE_AUDIT` for that clone. V3 derives strict order directly from each saved pair (`down[1] < up[0]`), reports the label mismatches, and exits 1 without changing the clone.

The untouched archive passes V3 with the retained 4 baseline false accepts, 0 candidate false accepts, and 15/85 cases per sweep. Four V3 tests, Python compilation, and the frozen V2 provenance audit pass. Commands and captured outputs are under `out/v3/`; `V3_RESULT.json` pins the V3 source and test hashes.

This validates saved-result chronology and read-only archive behavior only. It does not establish source truth, physical input timing, application consumption, game effect, threat response, recovery benefit, or MAP01 progress.
