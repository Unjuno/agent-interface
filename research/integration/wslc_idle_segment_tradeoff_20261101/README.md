# Append-only segmented history: staging/read tradeoff

Draft [#10074](https://github.com/Unjuno/agent-interface/pull/10074) isolates an
idle observation by copying retained `ObservationHistory` metadata. Earlier
[WSLc fork/disposal measurements](../wslc_idle_history_disposal_cost_20261101/README.md)
showed that cost grows with retained entries. This experiment asks whether a
restricted append-only, strictly increasing positive-integer map can reduce
staging cost by sharing immutable 256-entry chunks, and what it costs to read.

The prototype is **not a replacement for ObservationHistory**. It has no
arbitrary overwrite, deletion, image cache or artifact reload; values are shared
shallowly, as in the old dict copy. No code is integrated into the bridge.
Tests cover two-sided fork isolation, sparse monotonic keys, invalid keys,
chunk boundaries and shallow value identity; four pass in normal and `-O`
Python. They do not establish the full existing mapping or concurrency contract.

Each of four fresh WSLc allocations used the same pinned image, one CPU, 1 GiB
memory, no network or pull, with ascending and descending history sizes. Each
size has 41 paired trials with alternating order. Staging time includes fork,
one insertion and immediate staged-object disposal. Both sides use synthetic
metadata and the same small image; existing decoded caches are empty. Peak is
new `tracemalloc` allocation for fork plus insertion, not total resident memory.

| Retained entries | Dict fork/insert/dispose median, ms, ascending / descending | Segmented median, ms | Dict / segmented peak newly traced bytes |
| ---: | ---: | ---: | ---: |
| 0 | 0.0007 / 0.0006 | 0.0009 / 0.0009 | 936 / 904 |
| 1,000 | 0.0037 / 0.0039 | 0.0015 / 0.0015 | 37,696 / 2,984 |
| 10,000 | 0.0352 / 0.0316 | 0.0018 / 0.0017 | 295,736 / 1,832 |
| 100,000 | 0.6336 / 0.6709 | 0.0110 / 0.0104 | 5,243,704 / 11,408 |

The separate lookup experiment uses deterministic batches of 1,024 integer
lookups; it does not include image decoding or artifact I/O. At 100,000 entries,
the median per random lookup was 60.2 / 60.1 ns for dict and 414.7 / 417.5 ns
for the prototype; repeated access to the newest key was 20.3 / 20.7 ns versus
227.0 / 223.1 ns. Thus this restricted candidate trades cheaper staged copies
for substantially slower metadata reads. Small-size results and all raw samples
are retained, not inferred from the 100,000-entry row.

Both staging and lookup scripts were frozen before their respective two arms;
all four launcher exits were zero. Extract `raw.zip` into a new directory and
run `python staging-cost/audit.py` and `python lookup-cost/audit.py` without
optimization. They verify frozen file hashes, arm sizes/order, sample counts,
positive timings, medians and saved stdout/results. The archive includes source,
conditions, each sample, test output and launcher receipts. Main at freeze was
`8ebd9a107a284ea2270f9c846ff163f3f374043f`; the baseline history source matches
#10074 head `0675ab810f7ee890d0904b8a402678c81f8dbafb`. WSLc reported that its
memory limit did not include swap enforcement.

These microbenchmarks exclude source construction, capture, reload, IPC,
concurrent readers, model calls and task effects. Old reader references may
change actual lifetime and disposal costs. Root-tuple copying still grows with
history length, and retained metadata remains unbounded; no hard deadline,
general GUI speedup, cancellation safety, MAP01 completion or reliability rate
is established. Any adoption requires full mapping semantics or a justified
contract change, concurrency/cancellation validation and end-to-end comparison.
