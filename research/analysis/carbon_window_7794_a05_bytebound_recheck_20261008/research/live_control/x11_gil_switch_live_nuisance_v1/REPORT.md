# Live nuisance watcher: CPython switch interval 5 ms vs 1 ms

Task `X11-GIL-SWITCH-LIVE-NUISANCE-20260916-001`, Issue #413.

**Disposition: `LIVE_GIL_BOTH_SCOPED`.** Under the same synthetic same-interpreter CPU-bound Python thread, changing only CPython's switch interval from 5 ms to 1 ms materially reduced both native-watch observation gaps and deadline-to-verified-empty input release latency in this nuisance-only X11 fixture.

This result does **not** establish target-cue detection, a production/default switch-interval setting, hard-real-time behavior, arbitrary-GUI reliability, or shared-runtime promotion.

## Frozen design

Publication BASE: `f224cc42c083c9139185e3f89800fcd21bbea0a4`.

- 10 matched nuisance pairs / 20 cases.
- Native libX11 `XGetImage` acquisition; exact native 32x32 BGRX target-count predicate.
- Nominal watcher cadence 2 ms; owner authority deadline 600 ms.
- Nuisance render only; no formal target-cue cases in this rung.
- Fixture-local XTEST Right owner/release semantics inherited from the retained #231 path.
- Identical CPU-bound Python thread in the observer interpreter in both arms.
- Observer/Tk/owner/watcher guest CPU0; competitor guest CPU1; Xvfb guest CPU2.
- Arms: `sys.setswitchinterval(0.005)` versus `0.001` only.
- Pair offsets 150/152/154/156/158 ms repeated twice; arm order alternates.
- One formal block only; no retry, replacement, extension or post-data gate change.

Construction before source freeze established exact pixel/count equivalence at 0/1/511/512/513/1023/1024 target pixels, ABI/type guards, one excluded matched nuisance pair with verified release/final clear, and preformal mutation rejection. Construction timing was not used to tune gates.

## Frozen decision gates

Integrity is required: exact source/binary/schedule identity, exact pixel semantics, expected switch interval and affinities, positive competitor CPU exposure/cleanup, zero nuisance false cancellation, exactly one app press/release, verified empty final X11 keymap and final ROI clear.

Observation gate:

- median paired `1ms/5ms` maximum acquisition-start-interval ratio <= 0.60;
- at least 7/10 individual ratios <= 0.75.

Release gate:

- median paired `1ms/5ms` deadline-to-verified-empty ratio <= 0.60;
- median paired absolute reduction >= 0.5 ms;
- at least 7/10 pairs improve.

## Formal first outcome

All 20/20 formal nuisance cases completed once; 2,847 normal acquisitions were retained. False nuisance cancellation was 0/20. Every case retained exactly one app press/release, verified empty final keymap, final ROI clear, expected affinities/switch interval, competitor CPU exposure and cleanup.

| metric | 5 ms arm | 1 ms arm |
|---|---:|---:|
| median case maximum acquisition-start interval | 29.9689595 ms | 9.222917 ms |
| median case maximum acquisition-end-to-next-start gap | 20.5292265 ms | 6.4690185 ms |
| median deadline -> verified empty | 27.0606525 ms | 4.7188425 ms |
| median deadline -> release command | 1.3992895 ms | 1.9063695 ms |
| median release command -> XSync completion | 10.5774765 ms | 1.2685365 ms |
| median XSync completion -> verified empty | 13.0615065 ms | 1.361343 ms |
| median normal observations/case | 40 | 246 |
| median observation thread CPU/case | 3.3194085 ms | 15.428687 ms |
| median observation wall/case | 274.197161 ms | 352.4894465 ms |

Frozen paired results:

- median max-acquisition-start-interval ratio: `0.31390704917935774` — PASS;
- pairs with interval ratio <=0.75: `10/10` — PASS;
- median deadline-to-verified-empty ratio: `0.1921040676602045` — PASS;
- median absolute release reduction: `21.904422 ms` — PASS;
- release improved: `10/10` pairs — PASS.

Therefore the frozen decision is **`LIVE_GIL_BOTH_SCOPED`**.

## Interpretation

The release improvement is not explained by earlier command dispatch: median deadline-to-release-command was slightly *worse* in the 1 ms arm (1.9064 ms vs 1.3993 ms). The large changes occur after the command is issued: command-to-XSync and XSync-to-verified-empty both contract sharply.

Those segments mix Python/GIL scheduling, ctypes/Xlib interaction, X server scheduling/service and the verifier thread. They are not direct measurements of a GIL lock wait or pure X server service time. The intervention is CPython's global thread switch interval under this synthetic competing-thread workload.

The higher observation CPU total in the 1 ms arm is expected from the much larger number of completed acquisitions over the same authority window; this experiment does not claim lower total CPU consumption.

## Audit and retention

The frozen audit passes the formal result. The unchanged preformal test suite also passes after measurement. Fourteen direct mutations of the real formal raw result are rejected: switch interval, missing release, unverified release, acquisition timing, deadline, CPU sum, keymap claim, load affinity, zero load CPU, dead load, load cleanup, schedule identity, derived count and pixel payload digest.

Formal raw JSON: **1,113,523 bytes**, SHA-256 `5fa5c329ad129320e934a6ed7eccac42e9365403d86152bd31f9893348dc5121`.

Lossless XZ publication: **91,440 bytes**, SHA-256 `74702152788b155cf893b466e1dfca2eab786745de20df6c79062a0ce259715a`. Base64 publication chunks reconstruct those exact XZ bytes; `decode_raw.py` strips publication whitespace, verifies the XZ digest, decompresses, and verifies the formal raw digest.

## H / T / D / C / U

**H:** under the same competing Python thread, changing only the switch interval 5 ms -> 1 ms will reduce actual live-watcher observation gaps and deadline-to-verified-empty release latency.

**T:** one source-first frozen nuisance-only block: 10 matched pairs / 20 cases, first outcomes only.

**D:** `LIVE_GIL_BOTH_SCOPED`; both frozen observation and release gates pass with integrity intact.

**C:** switch interval affects interpreter scheduling globally. The post-command improvement may involve GIL scheduling, Xlib/X server interaction and verifier scheduling together rather than a single isolated primitive.

**U:** one CPython 3.13.5 / Linux 6.18.44 / Xvfb 21.1.16 / libX11 1.8.12 fixture with guest Intel Xeon Platinum 8573C topology, unpinned frequency and unknown physical-host isolation. Nuisance-only evidence does not establish detection of short target cues.

## Next rung

Do not change the shared/default switch interval yet. The next high-information rung is a separately frozen **target-cue** live integration using the same competing Python-thread workload and the same 5 ms vs 1 ms intervention. It should test whether the observation-gap headroom translates into preserved/improved 5 ms target detection while retaining verified release, without changing predicate, polling cadence or input authority semantics.
