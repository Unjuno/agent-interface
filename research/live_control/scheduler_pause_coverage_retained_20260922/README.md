# Pause coverage: retrospective evidence delivery (#4000)

**Scientific result:** `PASS_PAUSE_COVERAGE_COUNTEREXAMPLE_SCOPED`.
**Delivery scope:** the previous conversation's completed local experiment and
its failures, published retrospectively without executing another formal case.
This is not a Docker/OrbStack replication, runtime promotion, or task/model PASS.

## Chronology and immutable predecessors

Issue #4000 was created after measurement. Its timestamp is NOT a preregistration.
The archived freezes, commands, first outcomes and prior unpublished handoff remain
verbatim. Their old statements about unavailable writes describe the old session,
not this publication. New wrapper files describe only restoration/publication.

Original source/reference main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Continuation intake main: `d8358f6aa0211c660a0bd7c005174cb100e5eaad`.
Publication base: `b001dcd7b69389cd4060546028b811301fd0c83a`.
The closed #316 source Git blob is
`c0b349f313b97df59194db98ff6e792167239b5e`; the experiment calls its unchanged
`run_block(cpu, False)` rather than silently replacing the scheduler loop.

Three complete original namespaces are retained inside the archive:

| Original namespace under research/live_control/ | Disposition |
| --- | --- |
| scheduler_other_core_2547_caas_v1 | STOP_PARALLEL_CLAIM before formal timing when #3934 claimed #2547 |
| scheduler_pause_coverage_316_v1 | First worker completed its loop but stopped at unavailable procfs children metadata before scientific serialization |
| scheduler_pause_coverage_316_v2 | Separate fixed successor allocation, 12 cases / 3,600 primitive timestamp tuples, no reruns |

The v2 fix replaces only child-absence checking with waitpid/ECHILD under default
SIGCHLD. It does not alter the inherited loop, schedule or scientific thresholds.
All v1 failure bytes are retained. #493/#455 and concurrent #3934/#3949/#3954 work
are neither rerun nor modified.

## H / T / D / C / U

**H.** A complete count of 300 observations does not establish uninterrupted
sampling. After an external pause, the inherited absolute-deadline loop can catch
up numerically while old time intervals remain unobserved. This catch-up property
is already implied by source; the experiment measures its process/clock
manifestation, not a novel scheduling theorem.

**T.** Allocation `scheduler-pause-coverage-316-caas-20260922-02`, started
2026-09-21T19:31:01Z (2026-09-22 04:31:01 JST). Four cases each of no pause, 20 ms
SIGSTOP and 40 ms SIGSTOP, in the frozen balanced schedule. A fresh owned worker
runs 300 due/wake samples, nominal 2 ms cadence and 600 ms block; the first-to-last
due span is 598 ms. The controller stops only its own worker after 120 ms, observes
stopped wait status and procfs state, then sends SIGCONT. Retain PID/start-time,
affinity, source, raw timestamps, stop/resume brackets and terminal cleanup.
Formal invocations 1; retries, replacements and outlier exclusions 0.

**D.** Original PASS requires complete source/process/clock/cleanup evidence;
every paused case has a maximum gap at least pause minus 5 ms, at least five
consecutive post-resume gaps below 250 microseconds, and at least five empty
nominal 2 ms bins. All 12 cases returned exactly 300 samples and all frozen gates
passed. Independent raw-only audit errors are empty. An integrity PASS does not
imply general reliability or performance improvement.

**C.** Provided Linux x86_64 execution container, CPython 3.13.5; observer CPU 3,
controller CPU 4, no competing child. Frequency and physical-host placement were
not controlled. Docker CLI and engine/image identity were absent. No model,
provider, GUI, keyboard/mouse input, user data, network experiment, shared runtime,
scheduler policy or GIL default change. No GUI release attestation is claimed.

**U.** Four cases per condition, imposed rather than natural pauses. The result
cannot estimate natural interruption rates, actual transient-target misses,
physical input-release latency, model-useful feedback, tokens, human tempo or a
hard-real-time guarantee. Host scheduling, virtualization and clock calibration
are unresolved; no calibrated combined uncertainty or coverage factor is invented.
An empty nominal time bin is not proof that an application event occurred there.

## Original measured results

These are retained measurements, not freshly rerun benchmarks. Timing unit is ms;
counts are dimensionless. Every conversion from raw integer nanoseconds to the
following milliseconds divides by 1,000,000; no cross-clock subtraction is used.

| Pause | Cases | Min / median / max of case maximum interwake gap (ms) | Empty 2 ms bins per case | Consecutive post-resume gaps below 250 us |
| --- | ---: | --- | --- | --- |
| 0 ms | 4 | 2.350329 / 2.770661 / 5.104311 | 0, 0, 0, 1 | no imposed resume |
| 20 ms | 4 | 20.833236 / 20.909833 / 21.315663 | 9, 9, 9, 9 | 9 each |
| 40 ms | 4 | 40.811541 / 40.9867505 / 41.304553 | 19, 19, 19, 19 | 19 each |

The no-pause outlier remains in the denominator. Catch-up observations measure the
state at their actual wake times; they cannot retrospectively observe state in a
past gap. Sample cardinality, temporal coverage and useful task feedback must be
reported separately. No scheduling mechanism is selected or promoted here.

## Lossless packaging and independent revalidation

The original supplied ZIP had 105 files, 151,644 bytes, SHA-256
`03b0d24a320d8fe4de96aee798b1831f0ca2d72875e264718409c200256cf262`.
This publication stores a deterministic tar.xz representation, split only to fit
the connector's bounded write path. It restores the original file bytes and paths,
not the original ZIP container bytes. `MANIFEST.json` binds all seven parts, the
XZ and tar streams, all 105 extracted files and their canonical inventory.

All 102 entries across the three original checksum manifests pass (the three
manifests exclude themselves). A fresh restore produces 371,268 original file
bytes. Independent `audit.py` reconstructs all 3,600 tuples and reproduces the
original 8,056-byte audit byte-for-byte, SHA-256
`a8357ca1c2ba4cf1df451dbfb7bc7276f7bddb7c6246f619ee0f3d49bf13f3fa`.
The original 12 registered corruption controls and seven explicitly posthoc
envelope controls reject again. The original six construction tests are archived;
new `test_restore.py` separately tests six publication-only methods, including
five member subcases. These are not extra scientific observations.

`unpack.py` validates all content before creating a fresh destination and does not
execute archived code. It rejects occupied destinations, wrong hashes/counts,
nonregular members, traversal and unowned paths. Use a private trusted parent
directory; this is not a claim of adversarial concurrent-filesystem safety.

From repository root, in a fresh private scratch directory:

```sh
study="$PWD/research/live_control/scheduler_pause_coverage_retained_20260922"
work="$(mktemp -d)"
python -B "$study/test_restore.py"
python -B "$study/unpack.py" --out "$work/restored"
for d in scheduler_other_core_2547_caas_v1 scheduler_pause_coverage_316_v1 scheduler_pause_coverage_316_v2; do
  (cd "$work/restored/research/live_control/$d" && sha256sum -c SHA256SUMS.txt) || exit 1
done
cd "$work/restored/research/live_control/scheduler_pause_coverage_316_v2"
python -B audit.py formal-01 > "$work/reaudit.json"
cmp AUDIT.json "$work/reaudit.json"
python -B test_audit.py mutate-retained formal-01
python -B POSTHOC_ENVELOPE_CONTROLS.py
```

Do NOT run `experiment.py formal`, v1, or the consumed #2547 preparation. Read-only
audit is repeatable; the scientific allocations are not.

## Integration handoff and remaining roadmap

The concrete measurement constraint for #57/#2789 is that a complete observation
count must not be used to certify uninterrupted fresh feedback during local
control. The source/result hashes allow an integration worker to check this
constraint without trusting an aggregate PASS label. Shared runtime is unchanged.

Predecessor reconstruction, collision avoidance, local experiment, failure
retention and raw audit are complete. This PR delivers those bytes. Main readback
and own-branch cleanup require a successful reviewed merge, not this document.
The repository-wide roadmap and broad parent Issues remain open.

Transfer questions span real-time systems (gap-aware deadlines), sampling theory
(transients between observations), and distributed systems (producer capture time
versus delivery/acknowledgement time). The next meaningful empirical boundary is
an independently timestamped real state transition inside a sampling gap, followed
by a fresh, identity-bound consumer decision; no result here answers that question.
