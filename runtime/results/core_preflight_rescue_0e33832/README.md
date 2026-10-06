# Historical core-composition preparation rescue

Original remote source: `research/preflight-core-6866-45e9-20261003`,
`0e3383247855afbfef6013db50bd74763260d4de`.
The 15-file packet under `research/reviews/current_core_composition_6866_45e9`
is preserved byte-for-byte, including all 14 manifested files and the failed
first helper. This is archive integration, not adoption of an old production tree.

The independent read-only unittest checks complete manifest coverage and original
Git bytes, all 24 frozen source blob sizes/hashes, the retained combined contract,
both historical subprocess receipts, all 21 recording-backend session rows, and
the distinction between substantive command success and helper failure.

Historical results: 84 core methods passed; three valid inert sessions completed
once each; 18 invalid/expired sessions refused before preflight/execute. The first
helper exited 1 because it expected `ok` rather than `completed` (and a redundant
release call). Its failure record is an extraction, not independently retained
original stderr. Completion reviewed the same raw records without rerunning them.
These limitations are not repaired or upgraded by this rescue.

No historical helper, producer, formal allocation, or native backend is executed.
The local candidate commit/tree and private workspace custody claims remain author
claims, not independently reproduced merge/quorum certification. Current main's
later production repairs are left intact. Fresh archive checks and repository CI
are engineering checks, not fresh native effect or model-generalization evidence.

Run from repository root:

```sh
python3 -m unittest discover -s runtime/results/core_preflight_rescue_0e33832 -p 'test_*.py' -v
```
