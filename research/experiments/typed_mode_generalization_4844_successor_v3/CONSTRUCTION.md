# Construction log — allocation -03

All tests here use only construction seeds 59003/59004. Formal seeds 484431/484432 were not generated or read.

1. Initial host audit-construction test failed before freeze: the independent auditor expected JSON object key iteration to preserve the candidate's block declaration order. The candidate intentionally serializes canonical JSON with sorted object keys. Corrected the auditor to validate the block-key set while independently reconstructing and checking row order.
2. Final host checks: CPython 3.12.10 syntax compilation passed; `python -m unittest -v test_construction.py` passed 1/1. The test runs the candidate twice under the disjoint construction seeds and confirms identical bytes, 2,000 training rows, 4,800 heldout rows, 960 rows/block, 192 rows/mode in the COMPLETE block, and mapped truth labels. The independent auditor also reconstructs the alternate-seed data, validates all summaries/controls, rejects 16 mutations, and refuses noncanonical bytes and duplicate keys.
3. Final Docker Desktop checks used `desktop-linux`, cached image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` (`linux/amd64`), `--pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 --security-opt=no-new-privileges`, bounded `/tmp` tmpfs, and a read-only source mount. `python -m unittest -v test_construction.py` passed 1/1. Running-container inventory was empty before test; the container was `--rm` and completed normally.

This construction result is not formal evidence and contributes no rows or metrics to the allocation. An initial test defect is preserved here rather than silently erased.
