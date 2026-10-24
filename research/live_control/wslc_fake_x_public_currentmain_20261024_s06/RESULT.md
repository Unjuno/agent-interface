# Result S06

**HOLD — WSLc session and container started, but the container exited with code 1 and emitted no observable runner output.** The Fake X probe outcome is unknown; no PASS portability claim is made, and S06 was not retried.

The shorter harness path removed the prior pre-session WSLc initialization failure: the API reported WSLc 3.0.3, started the unique session, pulled the pinned Python image, and created the registered no-network container with read-only source/dependency mounts. The container exited with code 1 in under three seconds. Its captured output is only the UTF-8 BOM (3 bytes); no dependency verification line, probe result, audit, or runner summary was observed. The wrapper did not capture container stderr, so the exact startup failure stage is unknown. This attempt does not show that the probe failed its assertions; it shows no probe result at all.

Exact cleanup receipts confirm the one named container was deleted, the pinned image was deleted, and the exact WSLc session was terminated. Before cleanup, the sole file in its unique storage directory was `storage.vhdx` (203,423,744 bytes, SHA-256 `9cd93234be1b058f80c6db255158f720be02b222afbd8c6ed19525df44157641`). That exact file and then its empty parent directory were removed and verified absent. No global inventory or Docker command was used.

The source baseline and freeze remain `2166707229958e095d472c80e160c26449de7a29` and `d7b3d5477a4e4827bb7c5b490f24c3a71f266143b95eb2776e016eb46e1aa6d6`; all 67 mounted dependency files matched their hashes before launch. S05's pre-session HOLD remains a distinct immutable outcome. S06 says nothing about real X, physical input release, cancellation, recovery, GUI/application effects, MAP01, or live-control efficacy.
