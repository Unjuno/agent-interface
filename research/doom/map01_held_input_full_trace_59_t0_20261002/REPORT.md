# Full retained MAP01 v38/v39 held-input interval reconstruction

Allocation `MAP01-HELD-INPUT-FULLTRACE-59-T0-20261002-01` ran once on local Windows host CPU, 2026-10-01 18:11 UTC (Python 3.11.9). No Docker/OrbStack/WSL, GPU/CUDA, model/provider, GUI, OS input, or external effect.

## H / T / D / C / U

**H.** Applying the retained source-bounded analyzer to both complete event logs yields per-decision owner-commanded intervals, while exact physical key-hold duration remains unidentified.

**T.** At main `69a1bf509eb432e5e3c0c294d05ad7671d86adb6`, fetched and hash-verified the analyzer and both JSONL event streams. Ran the analyzer CLI exactly once per input. After both exited 0, a separate CPython process independently parsed the raw JSONL and recomputed all row intervals and aggregate fields; exact object equality against both candidate JSON outputs, complete row counts, and timing order were checked. Retries: 0.

**D. PASS_AUDIT_SUCCESSOR_SCOPED.** Candidate exits: v38=0, v39=0. Independent raw-only audit exit=0, errors=[].

| Trace | Raw rows | Completed holds | Verified interrupted | Requested total | Owner-commanded interval total | Overshoot |
|---|---:|---:|---:|---:|---:|---:|
| v38 | 340 | 11 | 0 | 3,600.000 ms | 4,233.849–4,377.563 ms | 633.849–777.563 ms (17.61–21.60%) |
| v39 | 634 | 27 | 1 | 8,930.000 ms | 10,544.035–10,873.310 ms | 1,614.035–1,943.310 ms (18.07–21.76%) |

These are per-trace totals, not a matched comparison. Median completed-hold overshoot bounds: v38 48.099–59.151 ms; v39 55.351–69.865 ms.

The single verified v39 interruption (`plan-3-primary-0-1`, step 0; requested 500 ms; keys Down+space) spans full-keyset acknowledgement to independently verified empty input: 212.580 ms. It is not an ordinary key-up timestamp and is kept separate from completed-hold totals.

### Per-decision ordinary completed bounds

Values are `owner-commanded interval [lower, upper] ms`; requested duration and interval width are included. Rows are in retained event order.

Machine-readable companion: [AUDITED_INTERVALS.json](AUDITED_INTERVALS.json). It is a posthoc transcription of this report's three-decimal row table plus the exact aggregate values captured in the run output; arithmetic consistency was checked without rerunning the candidate or auditor. It is not the original candidate JSON or raw auditor output.

| Trace | Decision / step | Requested | Bound (ms) | Width (ms) |
|---|---|---:|---:|---:|
| v38 | plan-0-primary-0-0 / 0 | 100 | 101.011–129.390 | 28.379 |
| v38 | cover-1 / 0 | 350 | 525.583–537.460 | 11.877 |
| v38 | cover-1 / 1 | 350 | 398.099–409.151 | 11.052 |
| v38 | cover-1 / 3 | 350 | 406.462–416.872 | 10.409 |
| v38 | cover-1 / 4 | 350 | 390.173–402.573 | 12.400 |
| v38 | cover-1 / 6 | 350 | 410.192–421.127 | 10.935 |
| v38 | cover-1 / 7 | 350 | 386.186–397.410 | 11.223 |
| v38 | cover-1 / 9 | 350 | 423.658–436.151 | 12.493 |
| v38 | cover-1 / 10 | 350 | 396.367–408.104 | 11.737 |
| v38 | cover-1 / 12 | 350 | 414.755–426.006 | 11.251 |
| v38 | cover-1 / 13 | 350 | 381.363–393.320 | 11.957 |
| v39 | plan-0-primary-0-1 / 0 | 350 | 413.755–424.241 | 10.486 |
| v39 | plan-0-primary-0-1 / 1 | 350 | 383.846–393.282 | 9.436 |
| v39 | cover-1 / 0 | 350 | 422.160–435.930 | 13.770 |
| v39 | cover-1 / 1 | 350 | 372.084–381.990 | 9.906 |
| v39 | cover-1 / 2 | 300 | 352.606–365.848 | 13.242 |
| v39 | cover-1 / 4 | 350 | 362.595–378.158 | 15.564 |
| v39 | cover-1 / 5 | 350 | 399.318–413.135 | 13.817 |
| v39 | cover-1 / 6 | 300 | 393.212–404.599 | 11.387 |
| v39 | cover-4 / 0 | 350 | 445.346–463.319 | 17.973 |
| v39 | cover-4 / 1 | 350 | 415.278–425.349 | 10.070 |
| v39 | cover-4 / 2 | 300 | 386.665–396.962 | 10.297 |
| v39 | cover-4 / 4 | 350 | 382.459–393.103 | 10.643 |
| v39 | cover-4 / 5 | 350 | 404.576–419.865 | 15.289 |
| v39 | cover-4 / 6 | 300 | 394.279–404.506 | 10.227 |
| v39 | cover-4 / 8 | 350 | 405.351–417.909 | 12.559 |
| v39 | cover-4 / 9 | 350 | 392.372–402.748 | 10.376 |
| v39 | plan-4-primary-0-1 / 0 | 180 | 258.489–271.292 | 12.804 |
| v39 | plan-4-primary-0-1 / 1 | 350 | 403.525–414.954 | 11.429 |
| v39 | cover-5 / 0 | 350 | 426.624–447.404 | 20.780 |
| v39 | cover-5 / 1 | 350 | 417.700–426.905 | 9.205 |
| v39 | cover-5 / 2 | 300 | 386.012–395.438 | 9.427 |
| v39 | cover-5 / 4 | 350 | 387.069–396.490 | 9.422 |
| v39 | cover-5 / 5 | 350 | 365.664–382.724 | 17.060 |
| v39 | cover-5 / 6 | 300 | 398.512–407.458 | 8.946 |
| v39 | cover-5 / 8 | 350 | 383.850–394.133 | 10.283 |
| v39 | cover-5 / 9 | 350 | 392.033–401.445 | 9.412 |
| v39 | cover-5 / 10 | 300 | 398.656–414.124 | 15.467 |

**C.** The interval is source-bounded *owner-commanded* X11 lifetime: the last in-hold artifact-ready event lower-bounds key-up issue, and the post-release capture upper-bounds key-up + XSync completion. It is not continuous `query_keymap` occupancy and an unobserved external key-up between samples cannot be excluded. Runs from different traces do not form a causal or matched comparison.

**U.** No exact physical held duration, useful task effect, safety, gameplay, causal v38/v39 difference, runtime speed, latency, human-tempo, or product claim. The distributions are small retained trace sets, not population estimates. This does not close #59 or replace #5156's owner-thread key-up instrumentation.

## Frozen identities and execution receipt

| Object | Path | Git blob | Bytes | SHA-256 |
|---|---|---|---:|---|
| Analyzer | `research/orchestration/o3-g1/measurement/analyze_held_input_telemetry_v1.py` | `092d622f0a3a617428ff990d275fbcad4b76da8e` | 8,784 | `fc81144b71eda448ace4baf93d07564c6549b45b04fb6ae3f992cb45a2f39710` |
| v38 raw | `research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl` | `02d65d49b61feadbdec2e051bd23d1ca845d5df1` | 308,873 | `80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3` |
| v39 raw | `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl` | `cbaeed9c7ba27b53cef9d10730ae33313371ad9a` | 565,849 | `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381` |

Candidate output SHA-256 (temporary files; see receipt limitation below): v38 `1e89a9e11726fa6f8e89088240b331000c60b5d622e7a06b438f12422e67a7ec`; v39 `259ce89ded0c880721e5f1899fc5c2e840dc1467d160bc315092b8fc0f937e2a`.

**Receipt limitation:** input/source and candidate result files were held in a temporary directory and deleted automatically after the run. The candidate result hashes and complete per-decision interval table above were captured, but the byte files are not retained. The independent auditor ran as a separate Python process from inline source; its exact source bytes and stdout digest were not retained. Thus the result is hash-bound to the frozen source and inputs and the audit outcome is reported, but the raw audit program/output cannot be byte-for-byte replayed from this PR alone. No second run was made to repair this evidence gap. The published independent table is the retained audit output.

Reproduction, if independently undertaken as a *new* successor (not a retry of this consumed allocation), should fetch these exact blobs and run the analyzer plus a separately stored raw-only auditor. Do not relabel exact physical occupancy or promote these bounds to live runtime evidence.
