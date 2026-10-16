# Native acquisition versus return-to-Python delay

**Disposition: `POST_NATIVE_DELAY_REPRODUCED_SCOPED`.** Issue #361; task `X11-NATIVE-RETURN-ATTRIBUTION-20260916-001`.

This is a completed component diagnostic, not a watcher optimization or shared-runtime promotion. With a CPU-bound thread in the same Python interpreter, most observed acquisition latency occurred after the C helper had finished its work. The matched separate-process competitor did not produce a comparable return-path delay. No input, owner-release, model or game was exercised.

## Provenance and bounded allocation

Publication BASE: `0a6012d189d2b4228d6f01462efc257e8d5e29dd`.
Source-first GitHub HEAD: `5fe3661620d52d8edf8fc4df6d47141b940b7c3d`.
Issue freeze comment: `5696517214`, posted before formal execution.
Result comment: `5696535287`.

All six frozen source/plan Git blobs were read back and matched local bytes before execution. The pre-frozen independent audit was not changed after measurement. One formal allocation executed; no retry, replacement or extension. The local `CONSUMED` marker prevents ordinary same-directory replay; it is not a distributed exactly-once guarantee.

The supplied local watcher-placement archive, SHA-256 `97095a226558dd5cac7ee0ba8706218d9407a59cdf3f6b86f36b34c7afae8c04`, motivates the unresolved acquisition interval. It is a separate predecessor, not pooled with GitHub #340 or this result. This experiment does not reconstruct its old approximately 6 ms outlier. No consumed allocation from #270, #283, #316, #330 or #340 was rerun.

## Intervention and implementation boundary

Three modes: idle; a separate CPU-bound Python process; an identical CPU-bound Python thread sharing the observer interpreter/GIL. The competitor executes the same calculation on CPU1 in both active modes. Observer CPU0, Xvfb CPU2, native helper, ROI, pixels, nominal 2 ms cadence, ordinary scheduling policy and 5 ms interpreter switch interval are fixed. Only competitor mode changes. Process versus thread also changes interpreter/address-space sharing; it is not a pure isolated GIL intervention.

There are six triplets with all six mode-order permutations, 32 acquisitions per mode, 18 cases and 576 acquisitions total. Each triplet uses identical static pixels; target counts are 0, 511, 512, 513, 1023 and 1024. Late nominal slots are skipped rather than filled by catch-up bursts. The sample budget is fixed, not elapsed case duration: active-thread cases take longer. No Tk event loop or task input is present.

The C helper records CLOCK_MONOTONIC before/after XGetImage and just before helper return. Python records the same clock before the ctypes.CDLL call, immediately after return, and after copying bytes. The helper validates depth24, 32bpp BGRX, 128-byte stride, little-endian image order and RGB masks, copies all 4096 bytes, then destroys the XImage. Unexpected ABI or invalid arguments fail closed. No subsampling, shared-memory extension or early predicate termination is used.

## Measurement definitions and units

| Field | Meaning / endpoints | SI unit and stored scale | Domain / type |
|---|---|---|---|
| `origin_ns` and row timestamps | One case origin and offsets for due, Python-before, C-enter, X-before, X-after, C-exit, Python-return, bytes-ready, scheduling decision | second; integer nanoseconds | Nonnegative integer scalars, common monotonic clock |
| `xget` | X-after minus X-before inside native helper | second; integer nanoseconds | Nonnegative duration scalar; includes native/OS/server waiting |
| `post_native` | Python-return minus final C timestamp | second; integer nanoseconds | Nonnegative duration scalar; not a direct GIL wait probe |
| `total` | Bytes-ready minus Python-before | second; integer nanoseconds | Nonnegative duration scalar; excludes later evidence hashing |
| `post_share` | Post-native duration as a fraction of Python-before to Python-return duration | dimensionless | Real scalar between zero and one |
| `X_thread_cpu_delta` | Native observer-thread CPU across XGetImage bracket and adjacent clock reads | second; integer nanoseconds | Nonnegative integer scalar; excludes X server CPU |

Unit check: report microseconds divide stored nanoseconds by 1000; ratios divide like-unit durations and are dimensionless. The independent audit checks ordered timestamps and the exact integer partition into pre-X setup, XGetImage, native cleanup, post-native and bytes copy. Medians of separate segments need not sum to the median total.

## First formal result

Numbers are medians of six case medians, in microseconds. Brackets show the range of those six medians, not confidence intervals. Each case has 32 calls, batch1, serial acquisition.

| Mode | Native XGetImage interval | C-exit to Python-return | Python-before to bytes-ready |
|---|---:|---:|---:|
| Idle | 70.596 [51.543, 88.663] | 1.077 [0.927, 1.713] | 79.602 [58.744, 98.518] |
| Separate process | 60.321 [54.006, 69.129] | 1.022 [0.852, 1.267] | 67.136 [61.142, 80.241] |
| Shared-interpreter thread | 96.881 [88.178, 101.968] | **5093.097 [5088.693, 5107.070]** | **5220.656 [5208.033, 5245.859]** |

The median of six case-median post-native fractions is **97.7924%** for the shared-thread arm. This denominator ends at Python return, before bytes copy. All six matched pairs pass all three frozen conditions: thread median post-native delay at least1 ms; median per-call fraction at least0.50; thread/process median return-delay ratio at least3. Required passing pairs:4/6; observed:6/6. All source, ABI, pixel, schedule, clock and load-integrity checks pass.

The maximum single-call post-native interval was5.289 ms in the thread arm. Rare native XGetImage intervals still reached1.431 ms idle and1.911 ms with the separate process. The native bracket itself is not a server-only service-time measurement.

## Interpretation: fact, inference, unknown

**Observed:** the induced delay is predominantly after native acquisition/copy/destruction in this workload; moving the identical competitor calculation outside the interpreter avoids most of that return delay in these samples.

**Inference:** shared-interpreter/GIL contention is a strong candidate explanation. The approximately5 ms return delay is consistent with the unchanged5 ms switch interval. The official Python3.13 ctypes documentation describes CDLL calls releasing the GIL during native execution and reacquiring it afterwards. This supports plausibility, not direct measurement of a lock-wait interval. Reference: Python3.13 documentation, `library/ctypes.html`, CDLL/PyDLL sections.

**Unknown:** how much of the final native-to-Python bracket is specifically GIL acquisition, residual C/libffi/ctypes work or OS scheduling; physical-host core mapping; attribution of old watcher outliers; live cancellation/release effects. No product speedup, pure server-time attribution or hard-real-time claim follows.

## H / T / D / C / U

H: a same-interpreter CPU-bound thread can dominate Python-visible acquisition latency after the native helper finishes, unlike the matched separate-process control.

T: seven static pixel/clock checks, three invalid-argument checks and one native2 ms pause clock enclosure; one excluded four-read-per-arm construction triplet; then the frozen18-case576-read block. A correctness preflight did not tune thresholds.

D: `POST_NATIVE_DELAY_REPRODUCED_SCOPED`, with6/6 qualifying pairs, versus the frozen minimum4/6. This is only a component mechanism disposition.

C: address-space/interpreter sharing, memory allocation, host scheduling, affinity and native-call processing are competing or interacting mechanisms. Timestamping introduces overhead in every arm; no calibrated overhead subtraction was performed.

U: one guest AMD EPYC9V74 environment, about2.596 GHz observed and unpinned, Linux6.18.44, CPython3.13.5 with GIL enabled, GCC14.2 -O2, libX11 1.8.12, Xvfb21.1.16,160x120x24. CPU0/1/2 are guest-reported distinct cores, not verified physical isolation. Cgroup quota400000/100000; throttle counters did not increase during the block. Six serial cases per arm and artificial sustained load do not support population reliability. No calibrated combined standard uncertainty or coverage factor is estimated; the reported ranges are descriptive only.

## Audit and complete raw retention

Before measurement, `test_audit.py` passes13 structural mutations, one derived-decision mutation and one coherent1 ns byte-identity check. The last is a cryptographic identity check, not structural detection of a self-consistent alternative timestamp. The same tests after measurement produce identical output. `validate_result.py` additionally rejects11 mutations of copies of the actual formal data/report. No audit source or formal result was repaired after measurement.

All12 competitors and the private X server were cleaned up. Full raw includes576 timestamp tuples, pixel bytes, source/binary identities, CPU affinity and measured CPU-exposure receipts. Child commands exited0. The surrounding shell's `TERM environment variable not set` text is separate from the successful experiment child.

Exact raw JSON:202432 bytes, SHA-256 `fb99faceca9715587bba3ec2b11cd2b5dcf8cde3b92c7559a6fd05da1e9b9e6f`.
Exact XZ:20448 bytes, SHA-256 `dca88f86fb0b670768b5cc46464934e6ab01765d4370837a2ba07a89c5f38afe`.
Executed native binary SHA-256: `e6412af00ec5242e74f82f92db510f06b41f8a8d42868ac00b49132cf6d9ad23`.

GitHub retains the full XZ stream in three Base64 parts, not just a result digest. `decode.py` checks each Git blob identity, joined XZ SHA-256 and decoded raw SHA-256. Remote part metadata at `7a8b5fcc34fd1316849549fdb6b99dcf2e7d047f` matched the locally calculated Git blobs. Clean-directory decoding of these byte-identical local counterparts reproduces the exact raw, independent audit, validation and native build. This was not a claimed network re-download. `publication_verification.json` states that verification boundary explicitly. The downloadable conversation archive additionally retains construction raw and the executed binary; source plus build recipe remains sufficient for a local rebuild on the recorded stack.

## Recompute without consuming a live allocation

From this directory:

```sh
python decode.py
python audit.py formal/raw.json --out recomputed.json --sha256 fb99faceca9715587bba3ec2b11cd2b5dcf8cde3b92c7559a6fd05da1e9b9e6f
python test_audit.py
python validate_result.py
```

These commands decode/review existing data only. `build.py` optionally rebuilds the native helper. Do not execute `run.py formal` for this consumed identity; a replication requires a new identity and plan.

## One successor question

Does changing only the interpreter switch interval from5 ms to1 ms in this same read-only shared-thread fixture proportionally shorten the post-native interval while leaving native XGetImage timing comparable? That would discriminate the GIL-timing explanation before adding process/IPC complexity or changing a live input owner. This next experiment has not run.

## Transfer and error check

Applicable disciplines: real-time control (a fast native operation can still return late to its controller), runtime/FFI engineering (native and interpreter timing boundaries differ), and experimental metrology (timestamps and treatment exposure require independent audit). Transfer benefits remain hypotheses.

ERROR CHECK: formal executions1; formal reruns0; source-first freeze verified; frozen audit unchanged;576 pixel/clock records retained; all load cleanup verified; no production runtime, input-authority, deadline or workflow edits.
