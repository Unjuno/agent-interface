# Same-author final source and saved-data review

No blocking defect was found in the minimal reader-guard composition. This is auxiliary work within the author's session, not a FINAL-v5 vote, independent application certificate, native remeasurement, or adoption disposition.

Final source6617B/SHA256 `9a1e4a31ae281e33f3e576dac4b78458e439c3b1d358afd9f9d2c64d7c1a5eb2` is exactly the previously inspected6513B source plus104B: two lines checking `reader.is_alive()` immediately after join and before/outside the journal condition. Every other production byte is unchanged. The adapted old test9613B/SHA256 `48c16f59db515cc6ba662260091826bac6d2ecc64bd308b914d53f320fca11e0` is exactly its9567B predecessor plus46B adding `RetiredReader.is_alive()` returning False. All seven old methods/assertions remain unchanged. New test11534B/SHA256 `fd4d68f28ebb4b4089e5deb38d9f5b26674b4f17cf39b075a3f8f02644f19f7f` is separately frozen.

The independent data-only reducer verifies prospective FREEZE/FIX times, command intents against receipts, every executed source/test image, both stream length/hash bindings,23 unique typed saved rows, and new native handle command/time envelopes. It never imports or invokes a client, test suite, native writer, or peer helper.

| Author's actual recorded command | Saved result |
|---|---|
| RED PID36240,09:50:00.634010–09:50:01.458259UTC |3 methods, exit1; healthy EOF passes, journal case records actual reader ValueError/frame loss, no-journal case records false normal return despite live reader. |
| Normal PID41988,09:50:36.300535–09:50:37.632188UTC |10 methods, exit0; all seven retained semantics plus three new methods pass. |
| Optimized PID39076,09:50:38.954431–09:50:40.068831UTC |10 methods, exit0; normalized typed semantic results match normal exactly. |

The retained controls preserve finite contended-journal refusal/holder-lock custody, healthy journal byte identity, no-journal and already-closed lock skipping, journal close's same exception instance/finally release, and explicit None join argument. New final held-reader rows report the exact reader TimeoutError with the journal still open and lock unheld; after one owned writer release, the valid notification reaches the cache and, when present, one exact received journal row. Later close returns normally; all recorded callers/readers are retired, parent/writer exit0, driver closes its pipe handles, and no driver kill is recorded. Source does not force `_closed` or mutate caches during the guard.

Six effective independently copied rows were rejected: Boolean parent-exit alias, fabricated normal guard return, journal closed while reader live, missing late frame, no-journal reader-retired relabelling, and integer alias for same-error-instance Boolean. Exact copies and reasons are retained in `final-saved-review.json`.

The reducer itself actually ran as PID35160,09:56:59.615487–09:56:59.885903UTC, exit0, source SHA256 `e6c54f8e8c7ab702a8d3a7c5a902d50305ea0a2445e94a0c0c33f9efab03eea7`. These are pure reducer process endpoints, not runtime/native experiment endpoints.

Practical limits remain: the new physical fixture uses a separately owned sibling writer and demonstrates notification delivery, not arbitrary descendant termination or a response-ID experiment. The response branch remains unchanged-source inference. A live reader with an already-closed journal is covered by unconditional source ordering, without a separate dynamic case. The None tests verify API preservation using a retired-reader double rather than physically measuring an unbounded wait. The per-phase timeouts and early-returning checkpoints do not promise a hard total close deadline. Journal `perf_counter_ns` values are not compared against the distinct monotonic close-clock domain. Concurrent send retirement, stderr EOF, parsing/reader-error propagation and pipe ownership remain separate contracts.

One preliminary final-test read used an incorrect guessed filename and failed before reading a file; the actual filename from the completed inventory was then read. This is an inspection path error, not a native/test outcome. No reducer first failure occurred. Earlier cp932 preview failure and every peer/author first outcome remain preserved. No GitHub send, Git/root source mutation, native subject-process replay, or model/UI/formal allocation occurred.
