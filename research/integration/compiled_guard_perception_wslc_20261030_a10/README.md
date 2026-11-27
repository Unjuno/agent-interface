# WSLc Calc compiled post-release settling: A10

One preregistered exploratory no-model Calc trial used candidate `2eb11a8ad6da315987a2438880791eb19878e83e`, explicit guard perception, and the public 500 ms post-release settle option. See `raw/conditions.json` for frozen inputs, image, command, and gates.

The graph recorded TASK_SUCCEEDED for one transition. The saved FODS oracle found 29, 31, and 899 with formula `of:=[.A2]*[.B2]`; post-action OCR read the same row. Physical key and button state was neutral, and the exact container ID was absent after exit. The retained settle receipt spans 500.094 ms on the host monotonic clock; the effect capture followed the recorded settle. Input file hashes match the preregistration.

This is one fixed-layout trial, not a reliability or speed comparison. The caller supplies `ready=true` and a manually selected window anchor. A fixed wait is not event-based readiness or a hard scheduler bound. The bridge has no independently verified close receipt. It does not establish MAP01 or general computer-control success. Preserve unsuccessful predecessor attempts A07 and A08.

All original trial files are under `raw/`; `SHA256SUMS` hashes each retained file other than itself.
