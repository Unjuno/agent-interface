# Status-cache snapshot binding — publication STOP

Issue #4403. Successor question to #4063 under #2084/#2789.

**Metadata only. Do not merge as a completed experiment or implementation, and do not close #4403.**

Disposition: `STOP_PRE_ALLOCATION_PUBLICATION` / `HOLD_PENDING_PERMITTED_PUBLICATION`.
Formal cases 0/36; formal batches started 0/6. No formal PASS is awarded.

## Question and H/T/D/C/U

H: a status snapshot read from SQLite can be tagged incorrectly if PRAGMA data_version is sampled only after acquisition. A before/after bracket on the same read-only connection may support safe historical-result reuse when both values agree, without repeated status SELECTs.

T: planned 36 cases, three policies, six commit schedules, two repetitions, three polls each. New cooperative private SQLite fixture, separate reader/writer processes, WAL/FULL and fixed query/database/connection lifetime. Supplied Linux x86_64, CPython3.13.5, SQLite3.46.1; Docker/gh absent, no image attestation. No model, GUI/input, user data, installation or experiment network. The fixture is not the production CLI or unchanged #4063 source.

D: excluded construction completed18 cases/54 polls/36 actor exits and six batch exits, all0. Separate raw-only construction audit1127 checks/errors=[], ten effective copied-evidence controls rejected. This remains PASS_CONSTRUCTION_ONLY. The public-source prerequisite failed before the declared formal allocation.

C: the token is connection-local, not a global database identity. A bracket does not promise currentness after its last sample; unrelated writes can cause conservative invalidation. Query identity, no same-connection writes and finite token lifetime are assumptions. The original three-case construction lacked the later cross-process timeline; no retrospective timeline is claimed. Initial source is retained locally with its original outputs.

U: formal acceptance, reconnect, database replacement, multiple writers, power loss, arbitrary application/model behavior, latency/token benefit and runtime adoption remain untested. Same-author separate implementation/process audit is not independent human review. No calibrated uncertainty or natural error rate is estimated.

## Excluded observations

Per six construction cases:

| Policy | Status SELECTs | All SQL statements | Obsolete cache hits |
|---|---:|---:|---:|
| ALWAYS_READ |36|72|0|
| AFTER_ONLY |14|53|4|
| BRACKETED |20|68|0|

All SQL includes PRAGMA and transaction commands. Counts are not time, I/O, tokens or task effects. The stale hits occur after a writer commits inside/just after the first coherent snapshot and before the after-only tag. The bracketed policy reloads on the next poll. These are directed construction observations, not a formal reliability claim.

## Operation-specific publication block

Issue/branch creation and registration of an unreferenced three-source tree succeeded. The next GitHub.create_tree request adding audit.py and controls.py was blocked with: "リクエストの安全性を確認できなかったため、このツールの呼び出しは OpenAI によってブロックされました。"

No additional reason was supplied. The blocked contents were not resent through another operation, path, encoding or capsule. Complete readable source/gate publication and Git-object readback were explicit prerequisites, so no formal command was run. The allocation was not relabelled local-only.

Tree466d85a18d6e0238586bec36e4eee0c619ab1005 is unreferenced and is NOT part of this branch. Creating objects does not establish reachable source or evidence publication. This branch contains only this README and two metadata JSON files; no implementation, raw corpus, audit code or evidence capsule is attached.

## Remaining roadmap

Permitted complete source/gate publication -> one retained allocation -> independent raw audit/controls -> complete evidence PR -> applicable exact-head checks/review -> qualified main integration. Local tooling/publication incidents remain in #4403, not separate research work orders. Keep this branch while the Draft PR depends on it. Previous studies, foreign branches, shared runtime and global ROADMAP are unchanged.
