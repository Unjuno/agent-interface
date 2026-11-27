# Hybrid observation-history candidate: integration and limits

The prior [segmented metadata experiment](../wslc_idle_segment_tradeoff_20261101/README.md)
did not implement the existing history's overwrite, deletion, cache or artifact
reload. This isolated candidate replaces only the record map inside the #10074
history snapshot: positive increasing integer additions use immutable chunks;
other keys, overwrites and deletes materialize an insertion-ordered dict. The
existing `ObservationHistory` validation, decoded-image cache and artifact reload
remain in use. It is not merged into #10074 or main runtime.

The normal observation path in the inspected #10074 bridge increments the
sequence and appends, while review and recovery clear history. This is a
code-path observation, not proof that every caller or concurrent interleaving
obeys append-only rules. Five new tests cover forks, overwrite/delete/clear,
numeric key equivalence, ordering and a seeded sequence of mapping operations.
With existing history, idle-observation and owned-process tests, **88 tests**
passed in each of normal and Python `-O` WSLc runs.

Two fixed-order private-Xvfb allocations exercised the candidate's actual
history class through an instrumented direct bridge. While a new observation
was staged, it remained invisible and minting it was rejected. In the cancel
arm it stayed unpublished; in the control arm it committed. Both then used a
fresh guarded owner to deliver `a` to an independent target, verify release
and leave X input neutral. The pause and concurrent direct-bridge inspection
are injected beyond the documented serialized-caller contract; no old held
input or natural failure was tested.

Two further WSLc allocations compare the real candidate and baseline history
classes using synthetic metadata and a 16×16 shared image, with two decoded
cache entries. Each size has 41 alternating paired staging/read trials. Staging
includes fork, insertion and immediate disposal; random reads are batches of
1,024 metadata lookups. Nine candidate overwrite trials separately time
materialization of the dict fallback, excluding disposal.

| Retained entries | Baseline staging median, ms, ascending / descending | Hybrid staging median, ms | Hybrid overwrite fallback median, ms |
| ---: | ---: | ---: | ---: |
| 1,000 | 0.00349 / 0.00327 | 0.00355 / 0.00270 | 0.0165 / 0.0159 |
| 10,000 | 0.0191 / 0.0187 | 0.00310 / 0.00323 | 0.225 / 0.143 |
| 100,000 | 0.404 / 0.409 | 0.0123 / 0.0132 | 1.773 / 1.807 |

At 100,000 entries, median random metadata lookup was 78.3 / 76.6 ns for the
baseline and 495.6 / 491.5 ns for the hybrid, per lookup after dividing each
batch by 1,024 (ascending / descending).
Staging is cheaper in this synthetic case, but random lookup and the first
fallback are slower. Setup, capture, disk reload, model, IPC, long-lived reader
references and full-session memory are outside this timing. The fallback and
the root chunk index still scale with history size.

**Known compatibility failure:** a post-run local probe starts iterating the
record map, inserts another key, then continues iteration. The baseline raises
`RuntimeError` because its dict changed size; this candidate instead finishes
the old iterator without an exception. The probe and output are retained.
This observable difference, untested arbitrary-key edge cases and lifecycle /
concurrent-reader guarantees mean the candidate must not be treated as a
drop-in replacement. Do not weaken tests to claim compatibility.

At freeze, main was `a83046e3fa0b66fb58d4356ca485474668852689` and the inspected
draft #10074 head was `0675ab810f7ee890d0904b8a402678c81f8dbafb`; seven named
unchanged source/test files were checked against that head. Manifests in the
archive pin the entire mixed snapshot. The real-X and cost trials used four new
WSLc allocations with one CPU, 1 GiB memory, no network or pull; the memory
limit did not enforce swap. The iterator probe ran separately on local Windows
Python and was not preregistered with the WSLc trials.

Extract `raw.zip` into a new directory, copy `audit.py` alongside its contents,
and run it without Python optimization. It checks source hashes, test results,
launchers, publication/cancel ordering, target effect and release, cost sample
counts and medians, and the retained iterator result. ZIP SHA-256:
`3cc1e5acb0518165f1905e50b8cb3621affa155d3568f5fc95d827f625499736`.
The benchmark and probe do not prove general speed, reliability, hard deadlines,
automatic recovery or MAP01 completion.
