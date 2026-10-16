# Receipt image selection

The receipt-clock self-use run guessed `007.png`; its terminal review actually
references `006.png`. `receipt_image.py` now selects the newest observation
sequence explicitly present in a received batch, including terminal reviews.
It resolves the referenced PNG inside an explicit run directory and reports its
capture time and SHA-256. Observation sequence is never converted to a filename.

`results/receipt-image-01` replays twelve recorded batches from three actual
self-use runs: nine image selections and three final batches without observation.
The modal images correctly differ between `007.png` and `006.png`. Four negative
controls reject a missing file, conflicting newest references, an outside-run
path, and a malformed newer observation instead of falling back to an older one.
Source and input batch hashes are recorded in `sources.json`.

The CLI was also used on the receipt-clock modal batch and the selected `006.png`
was visually inspected: Calc displays the format confirmation dialog. This is a
historical replay, not a new live trial or a demonstrated latency improvement.
Selection confers no input authority and does not refresh the capture. The hash
and later viewer read are not atomic; this is a local research helper, not a
complete arbitrary-input schema validator. Runtime paths must resolve in the
caller's filesystem (the current recordings are read inside WSL).

Run from the repository root inside Linux:

```sh
python3 research/live_control/receipt_image.py \
  research/live_control/results/receipt-clock-self-use-01/read-modal.json \
  research/live_control/results/receipt-clock-self-use-01
```

Next live use should pass the returned path to the viewer and measure the full
capture-to-effect interval, including errors and outer tool boundaries.
