# Complete receipt observation — Issue #4361

**PASS_RECEIPT_OBSERVATION_BOUNDARY_SCOPED:** 24 first-outcome sessions, 48 actor processes, three immutable eight-case batches. Research evidence only; no runtime/default or global ROADMAP promotion. REPORT.md contains the result and limits; SUMMARY.json is the compact index.

Correction to #4231 (comment5832396571): its receipt_ns was sampled by the owner before output, not by a receiving caller. Old evidence is unchanged and was not rerun.

## Read-only reproduction

SOURCE is the exact publicly committed preformal source/plan/proof/environment capsule (14 files). RAW retains all subsequent/excluded raw data and results (511 files). Together they restore all525 files /309470 bytes. Checksums commit integrity, not source authentication. The bounded restorer verifies both archives before creating a new output directory; it never executes archived code.

```sh
python -S -B restore_all.py /tmp/r5d3-review
cd /tmp/r5d3-review
python -S -B audit.py . > /tmp/r5d3-audit.json
cmp AUDIT.json /tmp/r5d3-audit.json
python -S -B controls.py . > /tmp/r5d3-controls.json
cmp CONTROLS.json /tmp/r5d3-controls.json
python -S -B -m unittest -v test_protocol
```

These commands do not execute the consumed formal experiment. Do not invoke execute.py on the old allocation. Full source including the independent auditor is inside SOURCE; protocol.py and actor.py are also directly readable and byte-identical.

## Interpretation

Producer emission, complete reader validation and effect-fsync brackets are distinct endpoints. A paused reader or a split frame can produce late observation despite an early producer stamp. A complete one-frame result need not wait for writer EOF. None of these observations certifies task success or permits input/retry.

Source-first commit:835ee200e7c5bbc3d381b1554f704c4371116f03, freeze comment5832600328. First result:comment5832623284. PUBLICATION_VERIFY.json records byte-identical restoration/re-audit and five packaging refusal controls. Same-author audit is not independent human review. Use a trusted quiescent local destination; this restorer is not a hostile-filesystem sandbox.
