# X11 PNG compute calibration uncertainty R7

Issue #1841. Raw-only successor to #1784; no X11/job allocation was rerun.

Decision: **PASS_X11_PNG_CALIBRATION_WAIT_ROBUST_SCOPED**.

## Source and evidence binding
The exact #1784 first RAW remains the parent evidence root:
`55d099ba71925692560d9b81e9ee65c39027af14133936b7d14026bf02a82e36`.

A compact paired ledger was derived only from primitive parent fields. Before inference it reproduces parent counts/sums exactly:
- stable g rows24, g_sum=353,425,454 ns;
- invalidated w rows8, w_sum=1,283,501,201 ns.

The authoritative analysis source is the hash-bound `SOURCE_BUNDLE.b64`; individual convenience text files are explicitly noncanonical after a preformal GitHub formatting mismatch. The bundle restores exact:
- PAIRS.json SHA-256 `938c5a9988c988308f22729ad5aaf468a4403d01fe8319c8134186e4901a1d78`
- analyze.py `7f8215b40775c1b3c08ab6f2a53e861673f204465242615f209d815b7fa6353f`
- audit.py `05b14d6caed0cb49f1f0c43144bd8e0a92982fa22d1fd06f367fed6cbe4bd3e8`.

## First analysis outcome
One deterministic analysis invocation; reruns/replacements/tuning0.

Stratified bootstrap:
- iterations100,000; seed1784001;
- each resample preserves 24 stable /8 invalidated draws;
- frozen authored p=0.25.

Break-even p*:
- 95% interval **[0.068676995, 0.101884375]**
- median **0.083743307**
- upper95 remains far below p=0.25.

Expected per-scenario RUN-WAIT cost at p=0.25:
- 95% interval **[+25.272517 ms, +33.347385 ms]**
- median **+28.977950 ms**.

WAIT is selected in **100,000/100,000 bootstrap resamples**.
Leave-one-out removal preserves WAIT in **32/32** cases.

Independent audit PASS; all four corruption/independence controls reject.

Exact result SHA-256:
- RESULT `40caf993813e24cb954262a749830841d273375ee8dfce060d4cda527564fe82`
- AUDIT `91fa7327ab450824cb85d84938f3b51470398a76ba6f3b6cdae749c1af818872`.

## Interpretation boundary
This closes sampling uncertainty only **inside the authored #1784 24/8 fixture**. It does not estimate natural deployment invalidation probability, natural reuse rate, alternative utility weights, other image entropies, host drift or production scheduler policy.

The correct next empirical question is therefore not another bootstrap: measure the same job class under a prospectively defined runtime trace/population if a deployment-relevant scheduler choice is required.
