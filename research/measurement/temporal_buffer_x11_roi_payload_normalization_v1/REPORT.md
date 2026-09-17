# A7 ROI XImage payload normalization + overhead — first outcome

Decision: `PASS_X11_TEMPORAL_ROI_CAPTURE_OVERHEAD_SCOPED`.

A7 is a fresh successor to consumed A6/#1067. A6 established a systematic mechanical failure: every fixed-quarter-ROI arm stopped after18 captures because frozen `bytes(img.data)` could not normalize a string-like python-xlib XImage payload. A7 preserves the A6 scientific capture contract and changes only payload representation normalization.

## Normalization repair

`normalize_image_data` is deliberately narrow: bytes are identity; bytearray/memoryview become bytes; str is encoded strict Latin-1; unsupported type, non-Latin-1 str, or normalized length other than76,800 bytes fails closed. Seven pure controls passed before source freeze. An excluded X11 construction ran long enough to cross A6's failure point and completed27 captures with exceptions0, observing actual payload types `bytes=22` and `str=5`.

## First formal outcome

One detached formal invocation, reruns/replacements/tuning0. Six fresh counterbalanced pairs completed the full frozen1.5 s interval. Every candidate arm captured31 frames, exceptions0, dropped slots0, exact ROI `[80,60,160,120]`, exact raw frame size76,800 bytes, and payload types `bytes=26,str=5`. The 500 ms ring remained11 raw frames /844,800 bytes in every candidate.

Candidate capture p95 by pair was0.779,0.508,0.645,0.780,0.473,0.920 ms. Candidate process CPU fraction was0.71%–0.94%. Paired fixture callback-count ratio p50 was0.9946808511, inside frozen `[0.97,1.03]`. Paired p95 callback-gap increase median was0.140865 ms, below2 ms. Maximum candidate-minus-baseline callback-gap excess was2.770 ms, below10 ms. Severe baseline stalls=0. Frozen audit errors=`[]`.

The formal result therefore closes the narrow A6 blocker and shows that, on this private Linux/Xvfb/python-xlib/Tk fixture, raw fixed-quarter-frame20 Hz XGetImage +500 ms ring satisfies the inherited overhead gates once payload representation is normalized losslessly.

## Integrity

Source-first GitHub readback matched all six frozen scientific blobs before formal. Postformal source rehash is exact. Five copied-result corruption controls are rejected5/5: task/region/invocation drift -> `FAIL_INTEGRITY`; payload type/length corruption -> `FAIL_PAYLOAD_NORMALIZATION`. RESULT SHA-256 `20ab82c169718cd6821841f49eed17940c006830c509b20ce598bd24fc89bfe3`; AUDIT SHA-256 `be6abe07d332c5119130bab38733246a2b630a978b495982fbc8d9741b9607d8`.

## Interpretation boundary / next discriminator

This is not evidence that arbitrary future-needed ROI is known at capture time. The next scientific question should not combine more optimizations. A useful fresh rung is region-selection semantics: can a declared/scoped moving or target-bound ROI remain provenance-correct when its source target moves or becomes invalid, while preserving this cost envelope? Alternatively, a separately owned cadence lane may answer the independent20 Hz->10 Hz tradeoff. Do not pool those factors.

## Scope

No model call, task input, real compositor, whole-desktop privacy, dynamic ROI discovery, XDamage, token saving or production latency claim follows. Fixed 160×120 ROI may omit task-relevant content; this result is capture-cost mechanics only.
