# A09 — layout-B OCR backend reproduction

## Question and decision

Does the frozen layout-B crop reproduce the three archived A05 OCR false negatives on the current local OCR stack, and does the padded crop change those outcomes?

**Disposition:** `UNCERTAIN_HISTORICAL_FALSE_NEGATIVE_NOT_REPRODUCED`. The full layout-B slice contains tasks 4–6 from both blocks: three originally `TASK_SUCCEEDED` and three `EXECUTION_INCOMPLETE`. Tesseract 5.5.2 read all six pinned images exactly with the padded crop, versus four of six with the frozen crop. All three historical failure images were exact with either crop on this host; among the three historically successful rows, the frozen crop was exact on one and the padded crop on all three. Both crops rejected the adjacent-task near miss on all six images. This supports the padded crop as a six-frame fixture construction, but it does not explain why the original A05 run omitted `t` on the three failure frames. The A05 C result remains 9/12; this construction does not qualify a live observer or authorize a new allocation.

## H/T/D/C/U

- **H:** Across the full six-task layout-B slice, the current runtime may reproduce the historical leading-`t` misses under the frozen box `(499,544,799,573)`, while candidate box `(493,539,805,579)` corrects them without harming successful cases.
- **T:** Read six PNGs from source commit `58bcbb4c45501880db8782158ddd3add3b765984`; verify source SHA-256; crop and 4x-resize with Pillow; run the adapter's exact Tesseract command on frozen and candidate crops; compare each output to its task token and adjacent-task near miss. `audit.py` independently reconstructs and reruns all twelve crops.
- **D:** Record each OCR output and crop hash. Reproduction requires at least one originally incomplete image to miss the exact token under the frozen crop and the candidate crop to recover it, with no new errors among originally successful images and adjacent-task near misses rejected. Otherwise disposition is HOLD/uncertain; never revise the consumed A05 score.
- **C:** The current host may use a different Tesseract binary, traineddata, OS image, or runtime than the original A05 host. The archived pixels and geometry can be correct while current OCR output differs. Four fixture frames do not establish general OCR reliability.
- **U:** The original host's Tesseract version, traineddata hash, and complete runtime provenance are not established by this check. No live GUI, provider/model, input, effect, authority, collateral, privacy, or efficiency property was measured.

## Reproduction

From a checkout containing the pinned source commit and Pillow:

```sh
python3 run.py > RAW.json
python3 audit.py RAW.json > AUDIT.json
```

The runner and auditor are local/read-only with respect to the formal allocation: they only read archived PNG blobs and write this package's output files. The tests do not start a browser, provider, GUI, input device, container, or study runner.

## Raw result

`RAW.json` records the exact command, Tesseract version, available-language evidence, all six source hashes, twelve crop hashes, stdout/stderr, exit codes, and OCR wall times. `AUDIT.json` records the independent rerun disposition and exact matches split by each frame's original task outcome. OCR wall times are single local invocations and are not a performance comparison.
