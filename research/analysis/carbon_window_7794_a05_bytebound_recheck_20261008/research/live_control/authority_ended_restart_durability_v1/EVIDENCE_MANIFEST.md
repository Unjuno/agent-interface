# Evidence manifest — authority-ended restart durability v1

## Canonical retained files

The namespace retains the final durable token source, its bridge dependency, offline/live preregistrations and results, the exact formal live runner and subprocess helper, compact live evidence, timing, and a GitHub-only audit.

## Exact source identities

Formal/live source files were read back from the branch and compared with locally computed Git blob identities:

```text
9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1  authority_ended_bridge_v1.py
  SHA-256 2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e

e48f4e2c1949ffd494a7e4e61510e9d3148aa646  durable_token_state_v2.py
  SHA-256 72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4

4495feebf13a00ff6bb1c4b723af11b64c33992b  ledger_child.py
  SHA-256 9d977d82d2507d7ecba6dfd3270e15d6d38d3cb7c6aa56bb7a345239d3ef6953

9d7b1022cf02246d23ec26d2d65502e10653e179  run_live_durable_restart_v1.py
  SHA-256 c6ea57e23494d350efba3bf8415b90681c3b8706dd1d36ea750af85af1cad857

a63183bca0d80220e83d29775ce32ca5d1f4b1bb  offline-prereg.json
  SHA-256 80ac902b586ff600403e9d9a1304b7bc2ccf5aaa6d47af88b20827dad4fa6e29
```

`live-prereg.json` is a content-equivalent publication copy whose whitespace/format differs from the locally frozen preregistration. The exact local preregistration is identified by SHA-256:

```text
117904f711f3c090d202f606ea95c484b6a4fd1a6d4100adfc9142e23f4fec00  prereg-live.json
```

The semantic fields and frozen source hashes are preserved in the published copy; byte identity is not claimed for that one file.

## Result identity / correction log

Local formal first-outcome identities:

```text
860765cf7e1e3b4f6bb0bb5ea709d2ba5f7c9c03b82bf33e5fd3e720774a2424  formal-result.json
938617707d9083d3708785542d2ac9277857924f1fb0be5b40b501047cbc8a3b  compact-evidence.json
86ec10dd899b00380610af3dc6842d776ad01b62c209d8da4a60464f87dcd18f  timing.json
```

During branch-only evidence publication, a manually transcribed `live-result.json` initially contained a second-release identity/timestamp from a construction run. Before any PR was opened, the branch copy was compared against the local formal result and the embedded `formal_result` in `compact-evidence.json`; those two local originals were exactly equal. The incorrect branch-only transcription was replaced with the formal first outcome (`second intent_token=b260152993594290b2a0946b3c9680b5`, `verified_ns=6351091940767`). This was an evidence-copy correction, not an experiment rerun or result change.

`live-compact-evidence.json` also embeds that same formal result plus the claim-relevant first/second terminals, the sole post-first-release input admission, final durable consumed state, final score/direct-final scorer sample and hashes of original raw text files.

## Raw live source hashes

The complete raw text files remain in the disposable experiment container and are not claimed retained on GitHub. Their identities are retained in `live-compact-evidence.json`, including:

```text
20fed76098eec378b0e4d0b4ab6e37e3695ad18a0a902e18d783bde982f2457c  events.jsonl
908c09e76b6ea2c9df725c998da490153e907cff4c0ed3bed3e5e719c08becf9  owner-events.json
a395bf5e8f0dc645577c5184bd02e8ddce2409531f3f64b95cd3bab3849c26ab  score.json
ad96428ac91b06cf3445fca84445d3e8800c36bd5b76e4d9dd602b878280481b  scorer-samples.jsonl
883159a0ebdbd910c72da031539ac298d95a28ba2452d2bb06c23817f64c265c  durable-token-state.json
```

`audit_retained.py` checks the offline 13-case result, live subprocess transitions, one-input admission boundary, final consumed state, release evidence, scorer equality, and these retained source hashes using GitHub-retained files only.

PNG/AIT visual binaries remain local-only and are not necessary for the restart/replay/release/input/scorer claims.
