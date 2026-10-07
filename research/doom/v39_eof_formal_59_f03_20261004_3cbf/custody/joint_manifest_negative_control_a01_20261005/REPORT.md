# Joint fixture/manifest mutation negative control A01

Status: `PASS_OFFLINE_PINNED_LINEAGE_REJECTION` for this construction only. The prospective F03 container-entry TOCTOU gate remains HOLD.

**H:** An offline verifier with a separately pinned historical manifest Git identity and authenticated source-tree witness rejects a source member changed together with that member's mutable manifest hash.

**T:** Run `python research/doom/v39_eof_formal_59_f03_20261004_3cbf/custody/test_freeze_lineage_v1.py` from the repository root on Windows Python. The test first reads the retained current-final eight-member archive, modifies one member, rewrites its SHA-256 row in a temporary copy of the freeze manifest, and invokes the exact lineage verifier. The decisive expected behavior is rejection on the manifest's historical blob binding. No Docker, formal producer, auditor, model, GUI, or game was invoked.

**D:** All five lineage tests pass, including exact retained archive/tree verification, single-member corruption, witness corruption, manifest corruption, and the new joint member+manifest substitution. Test exit code is 0.

**C:** A verifier that trusts only the supplied mutable fixture and matching mutable manifest would accept this internally consistent pair. The test's verifier instead compares the manifest against a separately pinned historical Git blob identity before trusting its member hashes.

**U:** This does not prove that the frozen F03 entry shell performs an atomic immutable snapshot or prevents time-of-check/time-of-use mutation between validation and `exec`. It does not change the formal freeze, authorize a container, rerun a consumed allocation, or qualify gameplay, GUI control, task effect, latency, safety, or production adoption. The prospective live launch remains HOLD until its exact entry boundary receives a fresh independent review and the specified prelaunch gates pass.

Source/runtime byte identities are in `SOURCE_SHA256SUMS.txt`; raw test output and exact command are retained beside this report. The verifier and archive were not modified by this experiment.
