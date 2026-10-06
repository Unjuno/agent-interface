# Relay JSON recursion-limit refusal

The first RED uses baseline commit b1ebb2ff275c8290dfa5659d247f1c91c46b663c
and the exact newly written tests before the runtime repair. Four methods yield
one portable-process failure and three decoder errors (array/object subcases
plus the post-acceptance case); the moderate-depth forwarding control passes.
The real portable SDK process exits1 on the deep line. Full first stderr/stdout
and command/source receipts are preserved, with disclosed private-path projection.

The source repair adds RecursionError to the existing pre-dispatch decode/envelope
refusal handler, before ID consumption. Candidate source commit
41fa8296b47884b1f1db6ca5315c0aa700e49126 passes all11 relay methods on Windows
CPython3.12.14/MCP1.30.0. The committed-source archive outside the checkout now
returns7 JSON lines and exits0: four refusals retain ID1, then actual SDK
list(ID1), validation(ID2) and explicit close(ID3) succeed. No GUI/input/backend
operation is invoked. The suite also preserves SDK content, accepted ambiguity,
no replay, finite/duplicate-key controls and frozen legacy protocol parity.

Exact source and test snapshots are under source/. First-red test bytes are
unchanged in behavior; only CRLF-to-LF normalization differs at commit. Archived
helper is .txt and never collected/imported automatically. logs/*.receipt.json
retain original child exit, timestamps and original stream hashes; PUBLICATION.json
separately binds path-projected files. Original logs/receipts remain private and
were not overwritten. No duration here is treated as a performance measurement.

All49 prior overflow/duplicate evidence blobs and47 old manifest entries remain
unchanged and verified through exact Git bytes. Their scientific/engineering
results stay scoped to their original sources; old176-pass/six-skip receipts are
not relabeled as a new all-runtime run. This package's current claim is the11-method
relay regression and one-line exception repair only. New head requires a new
content proposal; main agreement and exact-current-tree application remain pending.
