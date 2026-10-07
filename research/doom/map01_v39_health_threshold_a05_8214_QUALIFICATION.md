# A05 health-threshold evidence: preservation qualification

This note records a read-only qualification of the retained A05 package for PR
#8214. It is separate from the original package so its 28 Git blobs and
27-target `SHA256SUMS.txt` remain unchanged. It records no new candidate,
auditor, game, model, GUI, or input execution.

## Source hash and result hash are different

The preserved `RUN_LOG.md` labels
`9b72e814b085a00087739c5bf51e13f15fd8d2d14027993e0cb33a041e20fef5`
as "Candidate source SHA-256". That value is the hash of the saved candidate
**result JSON**, not the source program.

The exact stored-file identities are:

- `candidate.py`: Git blob
  `f447e0eaa3a2a15d65ba983b4739bc30d531cc15`; SHA-256
  `e75ac45a92062a98fd01e7b57043a18df7d30b26cff2a2e728439b6f219ad06c`
- Each `results/a01/candidate.json` through `results/a05/candidate.json`:
  Git blob `886b47ac652e0ccf47fa2ae2e28d6fa21a8451b6`; SHA-256
  `9b72e814b085a00087739c5bf51e13f15fd8d2d14027993e0cb33a041e20fef5`

The original manifest already assigns these hashes to the correct paths.
The historical log is preserved rather than silently rewritten. Correcting
this label identifies stored bytes; it does not retrospectively authenticate
which source bytes executed in a historical process.

## What the saved A05 evidence supports

Read-only inspection of the 640-event retained stream finds one source event
at sequence 204 and one monitor event at sequence 216. Both have observed
health 30; their capture times are 9111995907676 and 9113601498649 ns.
The report and saved A05 audit agree on those values and on
`health:source_expired`. The decision-5 pending interval contains 45 selected
health observations. The saved audit reports 25 checks.

The existing A05 `audit.py` correction binds the report's negative-control
values to unique raw observations. This note neither executes that auditor
nor claims exhaustive malformed-input rejection. The saved tamper-control
JSON reports exit 1 and no output after changing sequence 216's health to 29
and updating copied manifests. The complete mutated stream and process
streams are not included in this package.

The package contains selected A04 events, report and provenance files.
`raw-a04.zip` is referenced by hash but is not included; this read-only check
does not claim to have verified the full ZIP's bytes.

This remains one posthoc trace. No interruption was enacted here, and the
evidence does not establish improved feedback, control, survival, a live
scorer result, or an operational health threshold.

## Immutable references

- [Original #8209 source](https://github.com/Unjuno/agent-interface/commit/86547bc337dfae72efbbeff62fa30dc2a39a82a5)
- [Rescue source before this note](https://github.com/Unjuno/agent-interface/commit/9739c358c841a952766cdbb8d9ea10fbcc751ae3)
- [Original package manifest](map01_v39_unauthored_coast_health_threshold_replay_a01_20261005/SHA256SUMS.txt)
- [Unchanged historical run log](map01_v39_unauthored_coast_health_threshold_replay_a01_20261005/RUN_LOG.md)
- [Saved A05 raw join](map01_v39_unauthored_coast_health_threshold_replay_a01_20261005/results/a05/audit.json)

Both original and rescue heads retain package tree
`7daebe6a640a2616165d6c257e501838b1479f45`.
