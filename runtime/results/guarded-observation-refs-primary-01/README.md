# Primary use of lossless observation references

Seed 991336, Linux/X11 :147, Chromium target 6291459. The portable runtime was
built from ca53cefd9; its complete build manifest and artifact are archived.
All task actions used the public SDK MCP relay. Host callbacks forwarded complete
text and image blocks unchanged; no helper model, auto-targeting or action queue.
The primary agent read the local reference to source.native directly.

Six tasks across layouts A/A/A/B/B/B were independently scored correct exactly
once each. Entered values were visually reviewed before separate Save actions.
The planned old-reference control on task 4 refused before input and stayed full,
without observation references. Explicit same-image re-grounding then succeeded.
A full, unreferenced final result was retrieved, the connection closed with empty
held keys/buttons verified, and a referenced brief result with the identical
historical image was retrieved after close, without new input or capture.

29 calls: observation, two batch registrations, 22 completed inputs, one refused
input, two retained-result reads, and close. There were 24 referenced replies,
including the post-close read. Expanding only that lossless reference layer yields
123,025 UTF-8 text bytes versus the actual 111,193 bytes returned, a 9.6176% reduction.
This is a same-record metadata comparison, not actual model tokens, inference cost,
matched task latency or human tempo. It does not undo the separate lossy brief
summary of normal guards. All raw guards and images remain retained.

The fixture and transport exited 0. GUI children were terminal with codes 0/1/1;
this is not a claim of all-success child exits. The 514-file archive includes
all raw reports, delivered replies, source-bound review receipts, ordered host
events, independent submissions/oracles, cleanup, fixture source, runtime artifact,
relay/host sources and 255 protocol + 106 harness check logs.

Run `python -O verify.py` to audit identities, lossless expansion, raw guard/image
parity, exact-once values, review-before-Save ordering, refusal detail, release,
read-after-close and the actual returned metadata sizes. Prior replay evidence
remains under ../guarded-observation-refs-replay-01 and is not relabeled as live use.
