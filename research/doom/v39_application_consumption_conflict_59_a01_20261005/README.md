# V39 application-consumption contradiction A01

This CPU-only construction checks whether the V39 input-edge projector can emit an accepted adapter receipt while an outer event or nested measurement layer explicitly claims that the application consumed the input.

**H:** A receipt marked `adapter_edge_brackets_paired` and `application_consumption_observed: false` must be rejected if any duplicate evidence layer explicitly says `application_consumption_observed: true`.

**T:** Compare the frozen current #7602 projector at `8b5fa6429a1529bd98d61e8331a53c6fb76939e6` with the candidate. Mutate the outer event, measurement, adapter edge, and owner bracket on both rows of the retained positive A01 pair. Also test the unmutated positive and a 100-pair strict DOWN/UP interval sweep whose adapter brackets and sampling windows remain internally coherent.

**D:** PASS only when the baseline accepts at least one contradictory pair, the candidate rejects all eight mutations without exposing intervals, the valid positive stays paired, and each implementation classifies the coherent sweep as 15 ordered pairs and 85 incomplete pairs.

**C:** The retained A01 positive is an X-server keymap sampling bracket. It does not establish application consumption, physical dwell time, or useful task effect. This test is about truthful projection of explicitly present fields.

**U:** No live X server, game, model, or input allocation ran. OrbStack answered `docker info`, but its image list failed on an unsupported content-blob operation and the frozen `python@sha256:dddf…` image was absent with `--pull=never`. The candidate therefore ran on host Python 3.14.5. The ordinary module suite cannot import because Pillow and some sparse-checkout modules are absent; the runner AST-extracts only `input_edge_receipts`. This is source-bound construction evidence, not an integrated-runtime result.

The previous interval sweep updated the adapter interval and owner bracket but left their underlying pre/post sample timestamps unchanged. The current source also checks that chronology, so the sweep's 15 expected positive combinations failed in that form. The regression now moves the sample windows, request, sync and acknowledgement timestamps together with the bracket while preserving the strict-order decision.

The baseline/candidate raw comparison and saved-output audit are in `raw/A01.json` and `raw/AUDIT.json`. `FREEZE.json` records the exact source/input/script identities. The scientific result remains limited to deterministic projection correctness and does not close Issue #59's live threat-control, recovery, useful-feedback, per-key physical timing, or MAP01 gates.

The saved-result auditor independently derives strict ordering from each recorded DOWN/UP interval and has a mutation regression that swaps two recorded classifications while preserving the 15/85 aggregate. This checks saved-bound consistency; it does not establish that the bounds or raw observations are source-true.
