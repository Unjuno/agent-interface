# A14 immutable first-run ledger

Allocation: 5260-a14-wslc-model-review02-20261004.
Branch: research/5260-model-review-a14-wslc-20261004.
Frozen source: 0c2326209ad11f75046b643c958fba65856cd09b.
Base main at freeze: 358c17f4423785de3e38db48775cc6eb91cf334e.
Freeze time: 2026-10-03T20:39:42Z.
FREEZE SHA256:
91339f436ce0501ce3c5c4f738f1e710efdde44a33e8d03ce4ca9870a301b1fd.
Prospective #5260 comment5973281561; first result comment5973297464.

| First phase, 2026-10-03 UTC | Start | Finish | Exit | Wall seconds |
|---|---|---|---|---|
| candidate | 20:40:19.546752 | 20:40:26.603495 | 0 | 7.0559170 |
| host model | 20:40:33.099619 | 20:41:00.793181 | 0 | 27.6921673 |
| independent auditor | 20:41:23.024054 | 20:41:24.408375 | 0 | 1.3838142 |

Candidate raw SHA256:
392acfccb737608e80f516bfa59f8b1d0cf02d01defd37d944b80c26463fe605.
First audit stdout SHA256:
d62845b0c781be6f712eb620ad2401c2a80bdfc8712a8f5033b76cba86f76c81.
First audit errors[]; method METHOD_PASS_FINITE_REVIEW_ONLY;
hypothesis H_FAIL_FINITE_REVIEW_ONLY. Exit0 means valid method evidence,
not hypothesis success. Exact answers: true, false, true, true.

| Row | Request wall s | Input | Cached input | Cache-write input | Output | Reasoning output |
|---|---|---|---|---|---|---|
| 000 exact | 6.7114124 | 13596 | 12032 | 0 | 71 | 36 |
| 001 missing | 7.6229410 | 13841 | 0 | 0 | 33 | 0 |
| 002 decoy | 5.5959036 | 13841 | 0 | 0 | 61 | 27 |
| 003 ambiguous | 6.0990625 | 13854 | 0 | 0 | 88 | 55 |
| Column sums | 26.0293195 | 55132 | 12032 | 0 | 253 | 118 |

All four CLI processes completed exit0, timeout false, no tools.
Each had one fresh ephemeral thread, one original image and no retry.
The missing-prefix screen's requested label is hdv but actual TARGET is dv;
the model's completed valid answer instead says TARGET hdv and NO_REPAIR.
Neither this wrong answer nor the three correct answers caused post-review input.
No original source, prompt, schema, answer, raw trace or verdict was changed.

## Retention and post-run verification

All72 original files are copied byte-identically under retained/, including
private font-cache binaries/tags, screens, app/key observations and every
process attempt/receipt/stream. Original output directory is kept separately.
RETENTION.json records source/allocation and each original digest.
SHA256SUMS covers every packet file other than itself, excluding Python cache.
verify_packet.py and test_retained.py are post-run, additive, data-only
delivery checks, not retroactive gates for the first experiment.

TDD: six new verifier-dependent tests first failed assertions for the missing
verifier; the all-four clock corruption test already passed against the frozen
auditor. All17 then passed in a properly started private Linux display;
Windows16PASS+1displaySKIP. Retained status PASS_RETAINED_H_FAIL_ONLY.

Preparation corrections are kept distinct from formal outcomes:
- An image-inspect attempt used Docker's Go-template format, unsupported by
  WSLc; json format then confirmed the pinned image ID. No image was changed.
- A post-run Linux check without DISPLAY had16PASS+1SKIP. Setting DISPLAY=:97
  without starting Xvfb exposed STOP_READY in the construction test, 16PASS+1ERROR.
  Starting owned Xvfb/Openbox first yielded17PASS; no frozen source modification,
  new formal row, model call or formal allocation replay occurred.

WSL stderr SHA256:
2562006e62622bcf41c809d627cdc2c6250516b8cf1c9ccd28072c331fcc4096.
The kernel swap/cgroup warning and individual CLI shell-snapshot warnings remain
in original streams; enforcement and memory/speed improvements are unproven.
Only owned short-lived private containers/processes were used; peers untouched.
Full roadmap remains open. CI/review/PR/main delivery evidence belongs in the
subsequent GitHub delivery comment, not a rewritten first-result ledger.
