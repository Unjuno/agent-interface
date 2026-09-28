# Integration intake: lifecycle reuse reference-byte mismatch on Linux

Disposition: **HOLD_REFERENCE_BYTES_ON_LINUX** for promotion from this checkout.
This is an additive integration finding, not a revision of the original timing
outcome or a new scientific allocation. No production runtime change is adopted.

Follow-up: [exact-byte reconstruction](../lifecycle-reference-reconstruction-01/README.md)
passed all ten tests and reproduced the corrected raw audit in a separate copy.
Only two declared LF-to-CRLF mappings were applied, each matching its frozen hash.
This resolves the representation question for that derived copy; the original
Linux Git-byte failure and all evidence below remain unchanged.

At main `0c1e87b454fb70bcc7b11dbb8b6a719512d0425b`, the integration owner inspected
Issue #5133 and merged PR #5147. Its correction restores the five candidate
Python source files and supersedes the original break-even audit. To check the
published result independently on Linux, the owner exported exact Git bytes of
the v2 directory plus four required dependency/input files to a fresh local
source snapshot. This did not modify the checkout or any frozen evidence.

`python3 -B -m unittest discover -s <snapshot>/research/analysis/needle_role_skill_lifecycle_5133_v2 -p test_*.py -v`
ran 10 tests: 9 passed, one failed. Both candidate and oracle prediction tests
passed for 12,288 retained predictions. The failing source/reference identity
test reached lifecycle.py after validating the candidate source hashes.
The planned corrected raw audit was not invoked after the failure. No formal,
Docker, GPU, GUI, model or input allocation was executed.

## Exact dependency diagnosis

| Dependency | Git-byte SHA-256 | Frozen SHA-256 |
|---|---|---|
| research/analysis/needle_role_skill_lifecycle_4916_v2/lifecycle.py | e45a6b1ec6ad4995533c59d3ae560b9a91e2d31b2d7186c1cae5705f90602b80 | c03d07dd8b2b75e061609b72ceb9f258468a422bbf2d225acf4661e6d4f23282 |
| research/needle_role_skill_reload_3780_v1/loader.py | 5ff6df91ea3929f68fe77ccd6156bdb1310d0fec86088489d8b99905a7c5854f | 61c4439b3e1ee5ea19ba84b155043218a0bbd9ddaacc2ebf2338c1f046dbf863 |

For both dependencies, bytes from frozen base
`3007e03481d545eb9a92b8cec07c8c4201bd3728` and intake main have the same hash.
Converting LF to CRLF in memory reproduces the frozen hash exactly for both.
This is evidence of a line-ending representation mismatch, not code drift or a
contradiction of the stored timing rows. No transformed file was substituted
into the snapshot, no expectation was relaxed, and no test was rerun to obtain PASS.

## Integration decision

The five-source repair does not by itself establish dependency-byte reproducibility
for a Linux export. Keep the corrected synthetic timing result and this identity
failure distinct. A follow-up needs an additive, explicit exact-byte dependency
snapshot or a justified published representation mapping, then a fresh checkout
check and separately retained corrected raw audit. Do not overwrite the historical
FREEZE, raw data or audit to fit the current platform, and do not silently change
shared dependency line endings used by other frozen experiments.

Even after that gate passes, the result concerns a synthetic pure-Python scorer;
it does not measure this interface's capture/input/MCP lifecycle or justify a
production latency claim. The interface already offers explicit persistent X11
connections. Any further reuse should be measured at that actual boundary with
its ownership, cleanup and task correctness preserved.

The archive retains the complete selected source/input/result snapshot, original test log,
command exit record, reference diagnosis, source manifest and preparation scripts.
Use `python3 -O runtime/results/lifecycle-intake-01/verify.py` for a read-only byte
and disposition check; it does not rerun tests or execute archived source.
