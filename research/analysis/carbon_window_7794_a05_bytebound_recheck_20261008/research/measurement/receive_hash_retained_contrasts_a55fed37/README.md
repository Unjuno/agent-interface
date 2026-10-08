# Receive/hash: retained conditional contrasts (#2117)

**Original empirical result: HOLD_CUE_INTEGRITY. New result: verified posthoc arithmetic, not a new experiment or runtime acceptance.**

This publishes a compact, reproducible statistical view of the completed conversation-local Xeon allocation `receive-hash-handoff-20260922-04`, identified by source ZIP SHA-256 `a55fed37ce2d65e132577aa9c1f754f8229524faf3ccf5eb4413000f368afa74`. The different AMD branch `research/receive-hash-factorial-2117-v3-20260922` is not this allocation. Do not join results on short allocation ID alone.

## What was executed in this continuation

The original experiment was **not rerun**. A separately implemented standard-library reader decoded all 9,115 captured packets and 8,675 delivered packets, checked exact pixel digests, source/receipt times, delivery identity and the 384 cue widths, and reconstructed the 32-row input table. All 738 original manifest members and all 30 allocation04 frozen sources matched. The unchanged original lifecycle/raw auditor was also run read-only: exit 0, output byte-identical to its retained 76,460-byte AUDIT.json. Its empirical decision remains HOLD, not PASS.

The new analysis computes receiver and hash contrasts conditional on the other factor, separately for idle and busy. A second implementation uses Decimal arithmetic and coefficient matrices, without importing either the extractor or contrast implementation. Its 224 numeric comparisons pass. Sixteen unit-test methods pass, including 18 distinct negative variants (six are subcases of one method). These are same-author independent implementations, not external human approval.

The public PLAN commit preceded this new conditional-contrast analysis. The existing overall results had already been seen; this is explicitly posthoc and not blinded. The original experiment had a local freeze, not GitHub preregistration.

## Descriptive results: busy condition

Each entry summarizes four within-block contrasts. Brackets are the minimum and maximum across those four blocks, **not a confidence interval**. Completion coverage uses all acquired frames, including those never sent. Median latency uses only received frames and must be read alongside coverage and losses.

| Changed factor; other factor held fixed | 20ms completion-coverage difference, percentage points | Candidate/reference median-age ratio |
|---|---:|---:|
| Batch instead of single receive; whole hash | 73.8537 [48.0931, 94.5450] | 0.2211 [0.0684, 0.3927] |
| Batch instead of single receive; chunked hash | 54.1598 [8.3633, 91.6388] | 0.3065 [0.0566, 0.8859] |
| Chunked instead of whole hash; single receive | 20.3673 [3.2418, 41.4634] | 0.5881 [0.3149, 0.8138] |
| Chunked instead of whole hash; batch receive | 0.8412 [0.0000, 1.7336] | 0.6808 [0.5964, 0.7102] |
| Both changes versus single/whole | 74.5271 [49.8267, 94.8805] | 0.1535 [0.0408, 0.2789] |

The coverage interaction is -19.6939 percentage points [-39.7297, -2.9062]. The two improvements cannot be summed without conditioning: the gain from chunking is smaller after batching, where coverage is already near its ceiling. This describes this retained sample; it is not proof that one mechanism universally dominates or that all delay is GIL wait.

The combined paired median-age ratio above (0.1535) is intentionally different from the original **ratio of two group medians** (0.1008). Likewise, 74.5271 is the median of per-block coverage differences, not the original difference of pooled frame fractions (75.0701). Neither original number was corrected or overwritten; they estimate different descriptive quantities.

In idle conditions, the combined coverage difference is zero in all four blocks. Its paired age ratio has median 1.0626 [0.6801, 1.1637], so a universal latency improvement is unsupported. No frames are treated as independent experimental replications.

## Why the empirical HOLD remains

Exactly one cue, `b03-idle-batch_whole` cue 11, lasted **24,721,499ns**, outside the original 4,000,000-8,000,000ns interval. All 32 cases and that cue remain in this analysis. No removal, threshold relaxation, fresh seed or favourable replacement was made.

The busy batch/chunked cell delivered 1,136 of 1,137 acquisitions within the 20ms completion budget, yet only 23 of 48 cues were demonstrably received during their live display interval. Recent capture, current display, completed verification, and model consumption are different endpoints. This result provides no action authority or model/task success.

Original measurement environment: provided Linux x86_64 execution container; Intel Xeon Platinum 8573C; CPython 3.13.5, GIL enabled; private Xvfb; 32x32 BGRX (4,096 bytes); nominal 2ms capture cadence, 600ms case window, twelve nominal 5ms cues per case; four logical-role affinities plus a busy Python thread; unpinned frequency and host load. Source ENVIRONMENT records a 4-CPU cgroup quota. No Docker/OrbStack image identity, actual model/provider calls, or keyboard/mouse action. SOURCE.json retains the detailed original environment separately from this continuation's analysis environment.

## Reproduce the new arithmetic from this repository

Use Python 3 with standard library only; no installation, display or model required. From this directory:

```sh
python -B -m unittest -v test_analysis
python -B contrast.py --out /tmp/receive-hash-contrasts-new.json
python -B check_result.py cases.csv /tmp/receive-hash-contrasts-new.json
```

The output destination must not exist. The CSV is SHA-256 bound inside `contrast.py`. The generated JSON must have SHA-256 recorded as `analysis_result_sha256` in SOURCE.json.

### Availability boundary: original raw is NOT fully hosted by this PR

`cases.csv` is a **derived 32-case metric table**, not raw per-packet pixels, process transcripts or a complete original-source archive. It suffices to independently recompute every new arithmetic contrast. It does not suffice to repeat the original pixel/lifecycle audit. The complete original 5,886,413-byte ZIP remains a conversation attachment with the SHA-256 above; SOURCE.json commits to its identity without inventing a public download URL.

With that exact ZIP available locally, independently regenerate the table without executing archive code:

```sh
python -B reconstruct.py /absolute/path/agent_interface_receive_hash_20260922.zip /tmp/receive-hash-extract-new
cmp cases.csv /tmp/receive-hash-extract-new/cases.csv
```

The extractor reads ZIP/gzip data only, verifies all original member commitments, and refuses a different archive or existing destination. No consumed `run.py` or `manage.py` entry point is executed. Whole raw delivery to GitHub remains incomplete; this PR claims only the statistical view and outcome record.

## Variables, algebra and unit check

| Symbol / field | Meaning (日本語) | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| b | 対応ブロック番号 | 1 | Integer 0..3, analyzed within one load stratum | Scalar integer |
| s | 受信方式 | 1 | 0 single, 1 batch | Scalar binary |
| h | ハッシュ方式 | 1 | 0 whole, 1 chunked | Scalar binary |
| n_bsh / samples | 全取得画像数 | 1 | Positive acquired-frame count, includes unsent frames | Scalar integer |
| c_bsh / fresh_completions | 20ms以内の検証完了数 | 1 | Integer 0..received..n_bsh | Scalar integer |
| q_bsh | 検証完了割合 | 1 | c_bsh/n_bsh, within [0,1] | Scalar rational, not a population probability |
| M_bsh / median_age_twice_ns | 取得から検証完了までの中央値の2倍 | s (stored ns) | Positive sum of the two central ordered received ages; repeats the central value for odd counts | Scalar integer |
| T_bsh | 受信済み画像の中央値 | s | M_bsh times 10^-9 divided by 2 | Scalar real |
| Delta_B, Delta_H | 条件付き完了率差 | 1 | Candidate minus reference in one block | Scalar rational |
| I_b | 完了率の交互作用 | 1 | Difference between the two conditional receiver contrasts | Scalar rational |
| r_b | 中央値の比 | 1 | Candidate T divided by positive reference T | Scalar rational |

For fixed b and load, write q_sh for q_bsh. Define:

```text
Delta_B(h) = q_1h - q_0h
Delta_H(s) = q_s1 - q_s0
I = (q_11 - q_01) - (q_10 - q_00)
  = q_11 - q_01 - q_10 + q_00
  = (q_11 - q_10) - (q_01 - q_00).
```

The combined contrast decomposes along either path because the intermediate term cancels:

```text
(q_10 - q_00) + (q_11 - q_10) = q_11 - q_00
(q_01 - q_00) + (q_11 - q_01) = q_11 - q_00.
```

These identities hold per block; adding medians need not preserve them. The implementation verifies all identities with exact Fractions. The independent matrix calculation verifies their numeric outputs. Counts/counts and seconds/seconds are dimensionless; multiplying a coverage difference by 100 produces percentage points. No absolute monotonic timestamp is interpreted as a wall-clock date. Doubled medians retain half-nanosecond arithmetic without floating-point rounding of source integers.

## H/T/D/C/U, integration and remaining work

See PLAN.md for the public posthoc analysis plan. H concerns conditional contributions, T is read-only raw reconstruction plus all-block contrasts, D is integrity only while empirical HOLD remains fixed. C includes queue/backpressure, implementation, order and scheduling effects. U includes four-block sample size, non-random allocation, the cue-width miss, timing instrumentation and absent model/application endpoints. There is no calibrated combined uncertainty u_c or coverage factor k; extrema are descriptive only.

Concrete integration use: avoid treating a combined component contrast as two additive savings, and retain losses alongside latency. The next model-facing evaluation under #2117 must account for actual consumption and independent task effects. This analysis does not select a production default or close #2117, #2789 or ROADMAP.

Remaining delivery debt is explicit: the full original raw ZIP is not in this PR. Prior 01/02 STOPs and local03 startup STOP remain immutable; SOURCE.json identifies them and distinguishes the parallel AMD03 record. No new Issue was created for packaging or local tool failures.

Engineering incident retained: the first new-checker test run passed but emitted ResourceWarning for a CSV file not explicitly closed. A context manager corrected only that new checker; final 16 tests pass with ResourceWarning treated as error. Original experiment/auditor files were not edited.
