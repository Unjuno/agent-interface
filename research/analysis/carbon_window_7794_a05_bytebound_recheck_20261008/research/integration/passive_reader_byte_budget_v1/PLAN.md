# Issue 3977: whole-stream byte budget

Base: b2457b746a6df06f6536585dfe2ab937aff639f4. Parent #3876; closed #717 and prior #3883/#3917 remain unchanged. Owned branch research/passive-reader-byte-budget-20260922-v1; path research/integration/passive_reader_byte_budget_v1/.

## H
The existing experimental reader applies max_bytes to the whole retained stream, before cursor-prefix validation or record extraction. Prefix consumption and a smaller max_records cannot make an oversized stream readable. A preauthorized bounded increase with the saved cursor can recover only the unconsumed suffix; resetting the cursor redelivers the consumed prefix. This is the already documented host-decision boundary, not a vulnerability or upstream defect.

## T
One fresh 12-case formal allocation byte-budget-3977-20260922-01 in the provided Linux x86_64/CPython 3.13.5 execution container. No Docker CLI/image identity; no Docker/OrbStack parity, GUI/input, model/provider, installs or external-network calls in the experiment. Environment is in ENVIRONMENT.json.

Order: repetition0 then1; within each, total bytes1023,1024,1025; within each size, max_records1 then32. Each case has its own writer process, three ordinary DeliveryLedger.prepare notifications, complete LF framing and explicit prefix/append/stop handshakes. The exact archived reader and CLI execute in new processes under the package name upstream; this is only a packaging relocation, not public runtime CLI usage. No watcher, crash or producer-epoch change.

Seven reads per case: prefix at1024/32; fixed at1024/selected limit; diagnostic repeat of that same original cursor; explicit expansion2048/selected limit; empty continuation at2048; reset/no-cursor at2048/32; changed-prefix private-copy refusal at2048. All seven are registered comparisons, not failed formal-case retries. The prefix cursor and expanded cursor are separately retained. Timeout3s per CLI/handshake/normal writer exit; only owned child processes may be terminated on infrastructure failure. Formal output must be absent. Source freeze verified before output creation. One orchestration, no retry/replacement/tuning.

## D
PASS_WHOLE_STREAM_BUDGET_BOUNDARY_SCOPED requires12 complete cases/84 CLI calls/12 writer exits; below/equal budget reads return record3; all four oversized streams reject both fixed-budget comparisons with STREAM_READ_BOUND_EXCEEDED/exit2/no next_cursor; every expanded saved-cursor call returns record3 then empty/end; every reset returns records1..3; every changed-prefix copy rejects CURSOR_PREFIX_CHANGED; source/file/cursor/process/authority identities and independent raw audit reconcile; all10 rehashed corruption controls reject. Expected refused reads are not infrastructure failures. Complete contrary patterns FAIL; missing/source/process/timeout evidence STOP/HOLD. Never infer a producer terminal or ACK from an empty read.

## C and U
The producer and streams are trusted, private fixtures. No concurrent writes during a read, rotation/compaction, durable ACK, model consumption, task utility, exactly-once or production claim. Raising1024 to2048 provides finite headroom, not unbounded liveness or permission for automatic escalation. Clock timing is not a decision variable. Integer byte counts are exact; statistical combined uncertainty/coverage factor are not applicable. Host scheduling and independent replication remain unknown.

## Variable table and units
| Symbol | Meaning | SI/unit | Definition | Domain | Type |
|---|---|---|---|---|---|
| L | retained stream length | byte, non-SI information unit | exact len(stream bytes) |1023,1024,1025|integer scalar|
| B | caller byte budget | byte |max_bytes|1024 or2048|integer scalar|
| O | saved consumed offset | byte |cursor.offset|0 through L|integer scalar|
| R | return record limit |1, dimensionless count|max_records|1 or32|integer scalar|

Analytical boundary: if L > B, the implementation reads B+1 bytes, finds length greater than B and raises before considering O or R. Thus changing only O or R cannot bypass that gate. If L <= B, an unchanged prefix and valid sequence allow the suffix. All quantities in the length comparisons have the same byte unit. This derivation assumes a stable regular file during the read; the experiment tests this actual file/CLI binding, not arbitrary filesystem objects.

## Bounded roadmap
Source verification -> excluded construction -> freeze/publish -> one formal block -> external exit and independent raw audit -> corruption controls -> additive report/PR -> main readback and own-branch dependency-safe cleanup. The broad repository ROADMAP and #3876/#57 remain open.
