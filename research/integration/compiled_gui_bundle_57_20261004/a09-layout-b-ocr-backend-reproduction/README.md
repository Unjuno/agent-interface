# A09 — layout-B OCR backend reproduction

## Question and decision

Does the frozen layout-B crop reproduce the three archived A05 OCR false negatives on the current local OCR stack, and does the padded crop change those outcomes?

**Disposition:** `UNCERTAIN_HISTORICAL_FALSE_NEGATIVE_NOT_REPRODUCED`. Tesseract 5.5.2 read all three pinned failure images exactly with both the frozen and padded crops. On a fourth, matched layout-B image containing `t991073-4`, the frozen crop returned `1991073-4`, while the padded crop returned the exact token. Both crops rejected `t991073-5` for that control. The padding is useful for this control, but it does not explain why the original A05 run omitted `t` on the three failure frames. The A05 C result remains 9/12; this construction does not qualify a live observer or authorize a new allocation.

## H/T/D/C/U

- **H:** For the three immutable A05 layout-B failure screenshots, current Tesseract using the original PSM/whitelist command may still omit the leading `t` under the frozen box `(499,544,799,573)`. Candidate box `(493,539,805,579)` may correct it. A fourth successful task-4 frame is the positive/near-miss control.
- **T:** Read four PNGs from source commit `58bcbb4c45501880db8782158ddd3add3b765984`; verify source SHA-256; crop and 4x-resize with Pillow; run the adapter's exact Tesseract command on frozen and candidate crops; compare output to task token and a one-digit near miss. `audit.py` independently reconstructs and reruns all eight crops.
- **D:** Record each OCR output and crop hash. Reproduction requires at least one of the three failure images to miss the exact token under the frozen crop and the candidate crop to recover it, while exact/near-miss controls remain discriminative. Otherwise disposition is HOLD/uncertain; never revise the consumed A05 score.
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

`RAW.json` records the exact command, Tesseract version, available-language evidence, all four source hashes, eight crop hashes, stdout/stderr, exit codes, and OCR wall times. `AUDIT.json` records the independent rerun disposition. OCR wall times are single local invocations and are not a performance comparison.
