# Bounded decoded observation retention

The persistent guarded bridge previously retained every decoded full-screen
image in a dictionary, including its internal pre-input guard captures. It now
keeps two recently used decoded images. Older source metadata remains available;
explicit access reloads the exact saved PNG after checking its pinned digest and
dimensions. It does not capture a replacement frame. Missing/corrupt artifacts
refuse grounding. Window review clears history without loading old files.

This bounds decoded images owned by this cache, not total session memory.
Metadata, handle patches, disk artifacts and caller-held image references still
grow. Previously verified recent pixels stay cached. The original observation
sequence, pixel content, raw journal and model-facing image are unchanged.

## Validation

Source: `7c54a7baec54b8af3c8c464b5a873422a5ff8765`. Built archive SHA-256:
`b2267a588634feecec6b33d81f7528220eec67c0af06b14d9af8523f72094478`.
262 protocol and 111 harness checks passed, including eviction/collection,
exact-pixel historical grounding, artifact corruption/missing-file refusal,
metadata mutation, cache hits, clear and caller-held image lifetime. The first
check invocation had seven packaging errors because the new module was not yet
committed; its full failed log is retained. No source workaround was used: the
second invocation built from the committed revision and passed.

An exploratory storage comparison decoded the same retained 1280x800 screenshot
128 times into distinct RGB objects in each isolated process. Three pairs used
alternating dict/bounded order. At 128 images, measured `/proc/self/status` RSS
was 540324–540540 KiB for the former dictionary behavior and 39616–39824 KiB for
the bounded history (approximately 528 versus 39 MiB). Every arm re-read sources
1, 64 and 128 with exact pixel parity. This is one image, one host and a synthetic
retention loop; it does not measure whole MCP process memory, latency, useful
feedback, model tokens/cost or human tempo. The script's placeholder native raw
identity is construction metadata; the real input PNG digest is retained.

The primary assistant then used the exact built archive through public MCP in a
fresh private X11 allocation, seed 991338. The predeclared scope was task-1 only:
view source 1, request two newer observations, mint field/Save references from
evicted source 1, enter the value, visually review before a separate Save, close,
and retrieve original source 1 after close. All eight replies and explicit
review receipts are retained. Old-source minting did not advance source 3.
The independent submission journal records exactly one correct `t991338-1`.
The unchanged six-task oracle remains false with tasks 2–6 missing; this is not
a six-task pass. Input close verified no held keys/buttons; relay and fixture
exited 0. GUI child cleanup codes were 0/1/1, not uniformly zero. The new fixture
writes its independent submission journal directly into the allocation so a
future interrupted teardown need not lose the scoring prefix.

## Recheck

`python3 -O runtime/results/decoded-observation-history-01/verify.py` verifies all
139 archived files, reconstruction of the host timing, actual request sequence,
historical-source identity, review-before-Save ordering, independent task-1
submission, close, build identity and test receipts. It reads the archive without
extracting or executing its code. The memory rows are retained measurements,
not timings recomputed by this audit. No default wait or sensor is changed.
