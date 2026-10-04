# Timestamp-and-key admission/hold candidate count — A04

Status: `PASS_HEURISTIC_NONUNIQUENESS_SCOPED`.

## H/T/D/C/U

- **H:** For this retained v39 trace, later aggregate `keys_held` rows containing the same key do not uniquely identify every per-key `input_admission` row.
- **T:** On immutable hash-pinned `events.jsonl`, enumerate all later stream rows with event `keys_held` and matching key for each admission; independent auditor recomputes through a key-indexed scan.
- **D:** PASS only if exact source/counts match, at least one admission has multiple candidates, and independent raw audit matches every per-row candidate list and summary. FAIL if every row has exactly one candidate; HOLD on hash/count/audit mismatch.
- **C:** An undocumented serial-order or runtime relation may support a stronger reconstruction; this test does not use it.
- **U:** One posthoc trajectory, and only the explicit candidate heuristic. Candidate matches are not true identity. No physical key release/occupancy, useful effect, recovery, live threat control or MAP01 result is established.

## Provenance

Frozen against repository main `31ce02c0a148aed9650b58ef31a8746d5e85e091`; the trajectory stream is retained from its original source main `0ba1ef384965267c38a120f61977953636220fd3` and pinned at SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`. Commands, candidate stdout, independent audit and package hashes are retained in this directory. No game/model/GUI/input or container call is part of this analysis.

## Result

Candidate exit 0; independent audit exit 0. The raw stream has 634 events, including 39 `input_admission` rows and 28 `keys_held` rows. Under the frozen later-event/key-membership heuristic, 6 admissions have exactly one candidate, 33 have multiple candidates, and none has zero. The independent auditor uses its own key-indexed reconstruction and matches every candidate row, candidate histogram, and source/count invariant.

This result is sufficient to reject *that heuristic as a unique identity reconstruction for this trace*. It does not prove that a different algorithm using additional runtime artifacts or a verified ordering contract could not recover ownership. The earlier A03 package remains a HOLD because its decision gate/construction was invalid; A04 does not retroactively validate A03.

Protocol deviation: an unnecessary candidate/auditor replay was run during post-rebase integration verification, despite the one-run/no-retry freeze. Its parsed outputs are semantically identical to the first committed result and audit. The first result remains authoritative, the replay adds no evidence count, and the deviation is retained in `REVALIDATION_AFTER_REBASE.json`.
