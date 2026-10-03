# Retained hot-drain ownership audit v2

The original #6960 auditor accepted a copied CANCEL_ACK record whose control-reader FD was -1. It also ignored a later open event, accepting an additional owned descriptor group without its closure witnesses. Preserve the original first PASS/source/raw, and add a separately versioned saved-only verifier that rejects these two ownership contradictions.

This v2 adds only three predicates: open may appear only as the initial event; the selector FD is nonnegative; each pipe FD is nonnegative. Zero remains valid, exact integer/type and existing identity/byte/read-budget guards remain intact. The original15 directed rows,358 events,75 actual EBADF closure witnesses and hot-drain conclusions are unchanged. This does not show a leak or negative FD in the original native run.

| Symbol | Japanese meaning and definition | SI unit | Domain and assumption | Type |
|---|---|---|---|---|
| fd | 所有したpipeまたはselectorのファイル記述子 | 1 | 0以上; same recorded process lifetime; uniqueness and pipe inode joins also required | exact integer |
| births | 行に含む所有FD群の開始記録数 | 1 | fixed original two-pipe/one-selector protocol requires exactly1 at the first event | integer count |

Linux documents the nonnegative descriptor domain in [open(2)](https://man7.org/linux/man-pages/man2/open.2.html), accessed2026-10-03. The single-birth shape is already fixed in the unchanged original producer. No external implementation is copied.

Six ordinary pure saved-data methods,195 saved records per command:
- unchanged v1 RED: exit1,110 subtest failures (105 generated ownership copies,three exact discovered row copies,two exact full15 witnesses);
- unchanged test source against v2: normal exit0 and optimized exit0,zero failures; both195-record sets are typed identical;
- all75 negative-FD copies and30 extra-open copies reject; original15 results and75 logical FD0 positives remain unchanged;
- eleven earlier byte/type/ACK/cleanup/read-budget corruptions remain rejected.

The separately expressed FD birth/closure reference imports neither auditor nor producer. It verifies the original75 closed lifetimes,108 negative row copies (105 generated plus3 exact),75 zero-FD positives and saved-byte bindings. Its scope is descriptor ownership; preserved original byte-ledger/read-budget evidence remains separately bound.

Local ordinary command receipts contain actual argv/PID/UTC/exits/executed source/tests/stdout/stderr. The initial RED and pre-test arithmetic/placement correction remain. Internal helper analysis found the defects and is saved with explicit limits; it is not an eligible committee vote. The original consumed native allocation, candidate, driver, browser/model/GUI/input and auditor main were never replayed.

All new source/helper files end .txt and are not automatically imported or discovered. Exact raw is copied in inputs/raw.jsonl, SHA256242439e8d7a96f2c938668955c5469e40e1ccaeb97a754d1f1295e07f156efa0. Original68 predecessor Git images remain unchanged. PUBLIC_CUSTODY.json explicitly maps owned-path/runtime display projections; actual receipt stream hashes keep their private-original meanings. Private original helper/trace bytes remain retained, separately from public derivatives. The RED stderr public display is reversible base64 in evidence/red/stderr.log.b64 because exact unittest output contains trailing spaces. Decoding yields the recorded path-redacted public display; PUBLIC_CUSTODY binds both decoded and encoded bytes, and the original native stderr remains untouched. The first local whitespace failure and its original public images are retained outside the candidate. SHA256SUMS excludes itself.

Original #6960 is observed merged as38518811f537a5dc3dea3b231036b9006b25d8aa, then its source ref was deleted. The author sent zero main updates for that external merge; public records did not establish its worker-specific content-quorum/unique-application route. This repair does not retroactively certify that route. [Actual reconciliation](https://github.com/Unjuno/agent-interface/pull/6960#issuecomment-5967613964) confirms exact original content is retained on actual main.

The original PASS is historical and does not prove robustness to malformed ownership records. V2 provides only this finite copied-record correction. No private-original authentication, arbitrary malformed-family coverage, production adoption, natural-load/concurrent-producer/latency/task/physical-release/model/token/resource/full-goal claim follows. #17 remains open.

Fresh fixed-before-votes head/digest/committee, two actual eligible existing nonauthor votes, and later actual-current combined-tree/candidate/raw-commit/apply_id confirmation plus fresh rules/authority/owner/cancellation/objections and one forward expected-old application remain separate. No internal helper acceptance or old #6960 assignment/vote transfers.

For ordinary retained-data reproduction, the explicit regressions.py.txt accepts one new output-directory argument from this folder; reference.py.txt checks the saved normal/optimized evidence. They execute only selected pure auditor definitions. Do not invoke the original producer or any consumed allocation.
