# Additive custody clarification for the current-main compiled MCP recheck

This additive custody record documents retained-byte representations only; it does not alter the original packet or certify a new execution.
Prepared against exact main `3f8406516747304fe82d03a7d09cfed86ea9cd91` (PR #9242), read 2026-10-20 07:36–07:37 UTC.
The proposed additive packet consists only of these two files:
- `research/integration/standard_mcp_compiled_current_main_recheck_custody_20261020/README.md` (this note).
- `research/integration/standard_mcp_compiled_current_main_recheck_custody_20261020/CANONICAL_GIT_SHA256SUMS.txt` (supplementary canonical Git-byte checksums).

Every path inside the checksum companion is relative to the repository root, not to this sibling packet directory. Any later authorized checksum verification must resolve its entries from the repository root. The companion records the original packet's retained files; it does not replace its original manifest.
The original packet at `research/integration/standard_mcp_compiled_current_main_recheck_20261020/` and all its raw logs, conditions, README, and SHA256SUMS must remain byte-for-byte unchanged. This is a supplementary representation record, not a replacement manifest or a rerun.

## Exact representation mismatch

PR [#9240](https://github.com/Unjuno/agent-interface/pull/9240) retained LF raw-log bytes but recorded the SHA-256 of their CRLF representations. The existing [review finding](https://github.com/Unjuno/agent-interface/pull/9240#discussion_r4322447273) independently flags this same mismatch. The two explicit `-text` packet rules in `.gitattributes` do not reconstruct CRLF on checkout. Preserve the old manifest as evidence of what was recorded.

| Original relative path | Canonical retained Git bytes SHA-256 | Original manifest SHA-256 (CRLF representation) |
|---|---|---|
| raw/normal.txt | 2428f039f657bac67c18a97d9ea3812a82479ab5a69cb076921914a6606ae090 | 8ee8206afe4e6abb7bb0cf9bdcc598727e2e796057c8d0139ed8c8d7bd4c2993 |
| raw/optimized.txt | 462cdc20a9b56997680a981af10755fbfe43e3d817ee1ee8c0da870a78011af5 | 6915b75b90a7b015b10d4db97dd3533b0f2db5ff3737fbf64b7dd631fdb019d1 |

The original README and conditions digests match the retained bytes exactly: README `faef68badecb269ee8f8161429718c99e82748cf3ea13cef7ba27a6e1a4b587b`; conditions `5e583ae85482586987c53cb1735bf0f2b5b8e5fdd4ba73823957fb8067c167b1`.

The six conditions `source_sha256` entries likewise bind CRLF worktree representations, not the canonical LF Git blobs. The prior read-only lineage audit reproduced these digests by converting LF bytes to CRLF; the content identity is representation-scoped, not a functional source mismatch. Source pin is `577ddc30c918c422ddebab8a12eb133649fc789a`; the table's current-main comparison was verified at `41f1dc570a2affddece6ee894ed42d216b21a993`. These comparisons are prior verified evidence, not a newly executed test.

| Source | #9212 Git blob | Claimed-source/current-main Git blob | Canonical LF SHA-256 | Recorded hash = CRLF SHA-256 |
|---|---|---|---|---|
| [runtime/cli_v1/mcp_guarded.py](https://github.com/Unjuno/agent-interface/blob/577ddc30c918c422ddebab8a12eb133649fc789a/runtime/cli_v1/mcp_guarded.py) | 414e7bc01810c7469be218db98aed2afb235e181 | 80854871696dfbd553f8173ec3833000f6399ab5 | 7b899c7c1268e92bf343a757f1486830ffaaa7ddc03ce95614f52e3c91276347 | 191913c48207a80a5475a75e6edf36a3e64bd52a799b348c20ca4137d4aab41e |
| [runtime/cli_v1/mcp_server.py](https://github.com/Unjuno/agent-interface/blob/577ddc30c918c422ddebab8a12eb133649fc789a/runtime/cli_v1/mcp_server.py) | 67e00b8ac7db57d37a527c56b1111b82363e7896 | 67e00b8ac7db57d37a527c56b1111b82363e7896 | 6cb94623b10e7522df4b5745c38fb5060971d6425dafbaffe65606a243909b29 | 39e3d63b7eb25510ed5fadfc015f2bbc9614a0f2b32eaabbf07c57d4390a683b |
| [runtime/cli_v1/owned_guarded_session.py](https://github.com/Unjuno/agent-interface/blob/577ddc30c918c422ddebab8a12eb133649fc789a/runtime/cli_v1/owned_guarded_session.py) | 1c2ab030475a56629a5057943a1ade011e1ef11f | 5b6c9cac8a5dda0720174be8af6878bf051961c7 | c548e02b29b2db73b44407e8c764797111cc0851d0dc28974aa5ad63b5a38408 | acc9c378ddd88d75572071acfd612c76eaf282da9a918d52cb9da829b3890a1a |
| [runtime/cli_v1/test_mcp_owned_process.py](https://github.com/Unjuno/agent-interface/blob/577ddc30c918c422ddebab8a12eb133649fc789a/runtime/cli_v1/test_mcp_owned_process.py) | ed9dc43571aeab6dabe02f3b6adba78c9459a667 | 854532d5bc461c85757e8a2a7a896e3a404343e5 | 881ee0b9e1616f2f51dd26531db5b8d6335d1c15b840c462b845e7bee70fb9fc | 3f6bc4238b4d51dcb664c8bdca634ad7194f20bbe8ca220f3ca90c907b228745 |
| [runtime/guarded_x11_v1/compiled.py](https://github.com/Unjuno/agent-interface/blob/577ddc30c918c422ddebab8a12eb133649fc789a/runtime/guarded_x11_v1/compiled.py) | e3083d9d92e1a18cb8a695b7ce546eaac65dd6f9 | e3083d9d92e1a18cb8a695b7ce546eaac65dd6f9 | fc25aaf436b80cb531f1c77f8d23e237a268028491b3effc6e089b309662bf67 | ce3caf40d967c62df2d7eea06fc5def4db42c06c50f4ed30f345e5605f9ea8bd |
| [runtime/guarded_x11_v1/pixel_profile.py](https://github.com/Unjuno/agent-interface/blob/577ddc30c918c422ddebab8a12eb133649fc789a/runtime/guarded_x11_v1/pixel_profile.py) | 7f866f7fa4086e2f6402eca6c878c8dda96aba3b | 7f866f7fa4086e2f6402eca6c878c8dda96aba3b | 884c1cf46e42156dfec13d3d5efda9b13c979dd35d6e71d74808d67500553e87 | 10470c068aec22a6c7ab3fe9dcc1dba9ba6a5de2d70598a6aa660db0dbc7e121 |


## Scope and preservation gates

This note does not make the original SHA256SUMS pass, reconstruct original execution, independently certify its five-dot/OK logs, or establish physical release, live Xvfb/WSLc behavior, task success, reliability, recovery, or efficiency. The earlier #9212 full call traces belong to that earlier run, not this recheck. No source, experiment, input, tests, or CI was executed to prepare this note.

The fresh coordination read found no newer matching repair in the eight most recently updated PRs, no assignee on #9240, and no dedicated checksum-repair assignment in the current maps. This bounded observation is not an exclusive ownership claim. The maps still describe liveness-timestamp work requiring Linux verification; that work is separate. Unpublished work elsewhere is not ruled out.

WSLc #7924 remains STOP / HOLD: a zero-process snapshot is not owner release. Consumed A02/A03 and other prior allocations remain consumed. No common deadline was verified, no deadline is extended, and no new run, allocation, authority, or remote modification is implied.

Before any eventual integration, the authorized integrator must refresh main and live repair ownership/pending changes, compare exact preserved packet/source blobs against this base, and avoid duplicating a newer repair. Obtain non-author agreement on the exact additive diff and current composition. Any authorized main advance must be conditional on the freshly verified expected old SHA, must be a forward update, and must not overwrite concurrent work. If the base changes, re-evaluate the exact diff and evidence before proceeding. These preservation requirements do not establish any new execution, allocation, or scientific result.
