# Construction-only preflight record

Before allocation A06 was posted, the retained Chromium epoch-7 full-frame PNG was passed once on stdin to:

```
/run/current-system/sw/bin/tesseract stdin stdout --psm 11 -l eng --tessdata-dir /nix/store/jjybi6dzw9bcry2kl24axn414n1vpvxp-tesseract-5.5.2/share/tessdata
```

The observed OCR text was `@ Al FORM READY ... Observation fixture ... Value [ ... Save` (the ellipsis denotes omitted/uncaptured intervening content; this is not a byte-exact stdout transcript). The observed text did not contain exact substring `001101`. Original pilot stdout was not saved, so this is a contemporaneous summarized construction observation, not independently auditable raw evidence. It is not a formal candidate invocation and is not repeated. No A06 crop OCR was run before allocation.
