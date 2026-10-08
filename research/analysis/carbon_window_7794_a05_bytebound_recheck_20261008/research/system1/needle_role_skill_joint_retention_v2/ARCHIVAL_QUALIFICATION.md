# Archival qualification for the #4908 construction STOP

This additive archive preserves the exact 19 published blobs from [PR #4911](https://github.com/Unjuno/agent-interface/pull/4911) head [`504949f4381c8877d1673d327bdacd623e5eea11`](https://github.com/Unjuno/agent-interface/commit/504949f4381c8877d1673d327bdacd623e5eea11). It preserves a historical published record, not a verified reconstruction of the bytes used during execution. The original source, freeze, sidecar, reports, auditor, receipt, test logs and Docker logs remain unchanged.

The historical disposition remains `STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY`. The retained `7/7` zero-update test result and `PASS_STOP_EVIDENCE_AUDIT` remain historical claims; this archival inspection does not independently reproduce or certify them. It makes no training-quality or formal-result claim and does not close [Issue #4908](https://github.com/Unjuno/agent-interface/issues/4908).

## Historical claims and allocation boundary

[STOP.json](evidence/construction_01/STOP.json) records one invocation of excluded construction seed `736514`, an output-directory collision before fitting, zero formal fits, no raw, and no retry. The retained report treats the construction allocation `needle-role-skill-joint-retention-20260928-v1` as consumed. Its formal seed candidates `736711`, `736811`, and `736911` were recorded as unspent; preserving that statement does not authorize their use or establish their status outside this historical package.

[CONSTRUCTION_REPORT.md](evidence/construction_01/CONSTRUCTION_REPORT.md), [STOP_AUDIT.json](evidence/construction_01/STOP_AUDIT.json), and the original README contain stronger byte-readback and audit statements. They are left intact as historical evidence and must be read with the qualifications below. The later [publication-provenance addendum](https://github.com/Unjuno/agent-interface/issues/4908#issuecomment-5922704222) discloses source-to-invocation uncertainty. The [fresh successor #4929](https://github.com/Unjuno/agent-interface/issues/4929) separately preserves #4911 and the predecessor STOP/HOLD; this archive does not modify that successor or the original PR branch.

## Verified published-byte discrepancies

Only data parsing, byte counts, Git-object hashing, and SHA-256 calculations were performed. No retained source, auditor, tests, model, container, or experiment was executed, and no seed was consumed by this inspection.

### Seven source hash mismatches

Every entry in `FREEZE.json`'s seven-file `source_sha256` map differs from the bytes published at the pinned head:

| File | Recorded SHA-256 | Published SHA-256 |
|---|---|---|
| `runner.py` | `fbe71f641190b9200df8f9b6753c3dc95544e1917de2c0256c45a2cc5d5b5030` | `9e9a3c30daa8e09ce683002565ea8790ae12dbdd95f7f8fa29ebd91319e461d4` |
| `audit.py` | `faec87e671f9f1d9336781443f67c1ae8646f6d0884583a4dc75aaea15f97438` | `ea47aa49337623b303ee8a290218f9368099426b6ebe29e4a8cbf6a75786ba0a` |
| `test_construction.py` | `fe6de70d486eaa3f7799d57692b1fdfc3f95c01ec0ad6efb3127f6cc18e231aa` | `bd706f2f9e85d185a1e87540dfdd609282b928034cc2e7da66cf1c1fe3f8de89` |
| `construction.py` | `6c8724d17c381b4be5e600acec34f21677dd1a75777216b86c1087590d905996` | `97775befada92cf4c9591a98b538fef801de76bf01317ad2c0e3f7729e022415` |
| `construction_audit.py` | `b3747c7be25c5b8c31f6414146883a45685e6af965df06386bd53832b7d707ec` | `e97fccd366409aafa457c2535599f29ed4be3f3842f100b02fac58674b531b6e` |
| `PREREGISTRATION.md` | `992ba8b8d63556740c74270cdb275d3770a2db255af123e9af20a2351725cbbe` | `0ff41ff03f30c96564cebc2689ab5c60af6ddfeefbbb2e84317341905d35945f` |
| `README.md` | `03981c44cbbfc8adfe95af62e30f077766dbd547df9fc6c030b3615bf2c9b530` | `43d214e854f5f6cc4e036b4f7258c6096c5ac6da4e8fdc6442e8b41b1b0e98a7` |

### Freeze and sidecar

- Published `FREEZE.json`: `6d3c900c45737c362ed744cbbd7cec00eb1061b58ca34ae62a9dacb969c016fe` (1665 bytes)
- Digest recorded in `FREEZE.sha256`, `CONSTRUCTION_INVOCATION.json`, `STOP.json`, and `STOP_AUDIT.json`: `991f021b7f0e85785f847eaa16d692e487a1ebc62c0119dff236ee87d44cf581`
- Published `FREEZE.sha256` is 67 bytes: 64 lowercase hexadecimal characters followed by LF and then an extra CRLF. It violates the registered 65-byte lowercase-hex-plus-LF format and does not bind the published freeze bytes

### Receipt and logs

- Published `docker.stderr.bin` is 320 bytes, SHA-256 `caf6cba19f85e200ec63a10fd333269b8189f8499fa279cc0407a71a156ce732`
- The receipt records 318 bytes and SHA-256 `1474cec83c40291fb28d9d28cb5ce7bbef785c4477dd23b6015d8b23c8b9439e`; the retained STOP audit repeats that digest
- Published `CONSTRUCTION_INVOCATION.json` has SHA-256 `82253f907712e75ef1d520b297115001d38a9ddccc79b0241c5f93d0a4dd4c9e`, while the retained STOP audit binds it to `1ca4f592a85a331bae8920fe6e8b221fb2f34324aa0c8d6fc677daedb8807328`
- Published `docker.stdout.bin` is empty and agrees with its recorded zero-byte count and SHA-256. The stderr contains the historical STOP text; that alone does not establish its exact invocation provenance

### Image identity and local-layout limits

The invocation receipt's `image_id`, `inspected_image` text, and image token in `command_argv` use the 49-hex-character prefix `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e`. `FREEZE.json` declares the full ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`. The prefix agrees with that full ID but is incomplete identity evidence; this is not evidence that a different image ran.

The preserved `audit_stop.py` expects a local `src/` directory plus `outputs/construction-736514/`, but neither is included in the published subtree. Its raw-absence check addresses that local output path, whose historical contents are not in this archive. The current published layout and hashes therefore cannot establish the retained audit's execution context or reproduce its original evidence bindings. The recorded auditor path-fix attempt remains unchanged in [AUDIT_ENGINEERING_ATTEMPT.md](evidence/construction_01/AUDIT_ENGINEERING_ATTEMPT.md).

## Preservation contract

- Keep all original paths, Git blob IDs, modes and bytes exact, including newline differences and inconsistent metadata
- Do not normalize line endings, rewrite frozen hashes, repair the auditor layout, rerun the consumed construction allocation, or relabel the historical STOP or audit report
- Recovery of execution-time source or logs, if available from an authorized source, must be additive and independently identified. The discrepancies above do not establish which exact bytes ran
- Corrected execution gates or new temporal-quality gates require their own fresh successor freeze/allocation; this archive authorizes neither execution nor source adaptation
- This qualification and the separate parent index entry are new commentary, outside the historical 19-file set

## Exact retained inventory

The historical subtree Git tree ID is `4e07738d16051dbd27791ff19f59ca5b7b05cabd`. All 19 listed blobs were checked against the pinned tree by Git blob SHA-1 and byte length. This is an archival identity check, not a scientific or execution-provenance audit.

| Relative path | Git blob SHA-1 | Bytes |
|---|---|---:|
| `FREEZE.json` | `28962469bde9ccf629ec02a398e131773cb45ff6` | 1665 |
| `FREEZE.sha256` | `ef0217bb8dd688b420f4bb391942597560d775ab` | 67 |
| `PREREGISTRATION.md` | `84752e48d86280621515894d3e76c01d4b193428` | 2799 |
| `README.md` | `fff92172446af110df9b5a7faa8d9a373392b8e5` | 1748 |
| `audit.py` | `f0bc966a4e431603109c0bfc07a9802da28c723f` | 17062 |
| `construction.py` | `2cc8d64fd1f6839792606076cac442249d688747` | 933 |
| `construction_audit.py` | `582f5a58ca07c3406034964ccc53097984e88801` | 3780 |
| `evidence/construction_01/AUDIT_ENGINEERING_ATTEMPT.md` | `318270298d9243148566d9b8d0d3b6652984afad` | 436 |
| `evidence/construction_01/CONSTRUCTION_INVOCATION.json` | `0c4140b0ee6f2637cceabe5cb7e921c76f1c9713` | 1819 |
| `evidence/construction_01/CONSTRUCTION_REPORT.md` | `3d2d1a55da2e002996fa429e854add62cb8648da` | 1715 |
| `evidence/construction_01/STOP.json` | `dbec8638fef093eba72240b2c87ba275b81c7ee4` | 1849 |
| `evidence/construction_01/STOP_AUDIT.json` | `3c82b06e5f4b9648587f3f904f0a9071e90746f0` | 479 |
| `evidence/construction_01/audit_stop.py` | `dc60251a5dc07fc5496e3ae486f2c4b10f0f0a32` | 3132 |
| `evidence/construction_01/construction-tests.stderr.txt` | `dd0c15780c4d2eda2d6a6773395e46990968296f` | 1458 |
| `evidence/construction_01/construction-tests.stdout.txt` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | 0 |
| `evidence/construction_01/docker.stderr.bin` | `f7f34873395bf9fb11bc6b7d8a800993c97a3aec` | 320 |
| `evidence/construction_01/docker.stdout.bin` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | 0 |
| `runner.py` | `2ce9d4ac8960988206a9b2afd308b463e749c800` | 11379 |
| `test_construction.py` | `6d594b327ebbde6b6e2f49abb382c5e356f6aaa9` | 4851 |
