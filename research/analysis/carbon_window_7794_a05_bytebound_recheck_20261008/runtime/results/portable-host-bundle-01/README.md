# Portable host bundle construction

Build source `ee1535d14` (full revision in retained manifests). Python archive and public Node host modules were exported from the same committed revision, then used from cwd `/tmp` by the retained Node probe. The exported host launched the exported archive with Python `-I`, discovered public tools, statically rejected an empty program, explicitly closed the interface without opening a backend, and ended transport with exit 0. Three calls, no GUI/input/model, no replay. This is a distribution construction check; primary use of the promoted host is retained separately in `public-relay-host-01`.

The source-file and output hashes are retained, including the host-local manifest/checksums and exact requests/replies. The builder does not include host modules in the Python ZIP; they are adjacent files with a separate Node requirement. Distribution tests cover identical archive bytes with/without the option, exact committed host bytes, checksum agreement, and existing-destination refusal without changing outputs. No latency/token/cost/task-quality advantage follows.

Run `python -O runtime/results/portable-host-bundle-01/verify.py` to check retained bytes and the three-call outcome. This performs read-only reconstruction, not a new server/GUI allocation.
