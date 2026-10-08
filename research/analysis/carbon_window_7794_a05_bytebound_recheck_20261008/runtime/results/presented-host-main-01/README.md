# Presented host calls integrated onto main

A portable runtime built from merged main could not run the reviewed caller:
the exported instrumented host lacked `sendPresented`. The caller stopped before
dispatch, closed its transport, and produced no application effects. This report
retains that failure and a fresh personal GUI trial after integrating the existing
candidate host APIs onto main. The whole candidate branch is not adopted.

The host can now send one request and present its unchanged original text/image
content under one reservation. Another send, review, or close cannot interleave
between those stages. `wait()` reconciles the same outstanding operation without
resending it. A presentation failure preserves the reply and blocks ordinary
continuation. Retained replies must still match their original delivery digest.
Explicit text acknowledgments attribute the caller to already presented text;
they do not replace image review or certify understanding or task success.

Source: `ddc9bf5c438520baae4eac391e7c0f5e0f4af578`, based on merged main
`49db21e330768800e8b3486203b70306f4e402f6`. The host implementation is copied
from the previously tested candidate; the timing reader accepts its separate text
acknowledgment event. The CI host suite includes the new acknowledgment tests and
the existing evidence-capacity tests.

## Retained checks

- Tests before the host port: 11 failures among 40 host tests. After the port:
  40/40. The timing reader's new acknowledgment tests also failed before its port.
- Shared local native checks: 335 protocol tests and 148 harness tests.
- Personal trial on WSL 3.0.1 / Ubuntu 24.04.4, private Xvfb/Openbox/Tk fixture:
  first click transfers focus to B; the guarded text operation stops at op 5 and
  releases input. The caller reviews the actual image, explicitly activates A
  with `review_after_activation=true`, reviews the fresh image, grounds a new
  alias, and types `z`. Original application key events contain exactly one `z`
  for A and no keys for B. Public close has verified neutral input, transport
  exit is 0, and all three owned children are terminal (one terminated by SIGTERM).
- Original PNG bytes in all four public replies match their retained artifacts
  and review receipts. Both trials' pre-run plans and frozen build hashes remain
  unchanged. Portable module hashes and source revision are checked.
- The raw-only archive verifier passes normally and under `python -O`. Changing
  the independent journal's input recipient to B is rejected in both modes.

The trial planned 8 public requests but issued **9**, because the first clock
sample elapsed during schema inspection and one new sample was taken before
activation. There was **one additional retained-PNG preview** following context
continuation. Both deviations are explicit; the extra clock was not an input or
failed activation retry. This is a known-fixture personal replication, not a
preregistered matched performance comparison.

The measured first-send-to-last-reply host span was 310,774.62 ms, including
1,841.16 ms with requests outstanding, 10.39 ms in presentation callbacks, and
308,923.06 ms in other host intervals. Those other intervals include orchestration,
logging, context continuation, and caller gaps. They are not isolated model
reasoning or waiting. This establishes scoped working behavior, not human tempo,
first useful feedback latency, semantic completion latency, or speedup. Actual
provider tokens and cost were not measured in this trial.

## Verify without a live desktop

```sh
python runtime/results/presented-host-main-01/verify.py
python -O runtime/results/presented-host-main-01/verify.py
```

`raw.tar.gz` contains 185 original files, including both frozen trial builds,
host request/reply/presentation records, original images, application journals,
cleanup, RED/green/full native logs, and the WSL environment check. Its member
inventory and hashes are in `raw-manifest.json`; `result.json` binds the archive
and auditor. Verification extracts only declared regular members, checks bytes,
and recomputes the scoped result from retained raw records without GUI input.
