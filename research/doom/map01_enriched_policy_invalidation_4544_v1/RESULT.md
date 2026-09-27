# #4544 local construction result — enriched monitor receipt

**Disposition: `PASS_ENRICHED_POLICY_INVALIDATION_RECEIPT_CONSTRUCTION_SCOPED`.**

## Outcome

The actual `ObservableSignalPolicyMonitor.observe()` implementation emits the
expanded envelope described in #4544. The translator accepts that
production-shaped event, preserves the full event and outcome (including
unknown future metadata), and adds explicit host/runtime provenance without
mutating the input. The old mixed-domain call raises the retained
`controller decision precedes observed boundary` error. Translating the
synthetic host boundary using the latest-possible offset makes final admission
return `REJECTED_POLICY_INVALIDATED`, with no executor admission and no input
authority.

Thirteen deterministic cases pass on both the host and local Docker. Two
intermediate fixture/test attempts failed and are retained in this narrative:
the first host attempt had 10 passes and one error because the monitor fixture
used the machine's live performance counter while the ordering gate used
retained synthetic timestamps; a later over-width case initially changed only
the declared offset, which the new raw-probe reconciliation correctly rejected
before reaching its intended uncertainty assertion. The fixture clock was
then frozen at the test seam and the over-width case changed the raw probe
value consistently; no production code or decision gate was relaxed to obtain
the passing result.

## Verification

Host:

```text
python -B -m unittest discover -s research/doom/map01_enriched_policy_invalidation_4544_v1 -v
Ran 13 tests — OK
```

Local Docker Desktop, cached image
`python:3.13.5-slim-bookworm@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`
(`linux/amd64`), `--pull=never --network none --read-only`, read-only source
mount and 16 MiB `/tmp`:

```text
Ran 13 tests — OK
```

No network, model inference, GPU, input command, or gameplay claim was used by
the receipt tests. A separate local, offline zero-decision preflight now also
passed. The issue-specific `linux/amd64` image was built on this PC from a
pinned Python base, exact dependency versions, and Freedoom archive/WAD SHA-256
checks; its local image ID is
`sha256:d9ceb63e8eb71c82a0094a6d0c44bb6d60a9e7e3f635211fa6f1fc2409511ff7`
and reported size is 1,140,033,132 bytes (1.14 GB). The image runs ViZDoom
1.3.0, MAP01, skill 1, ASYNC_SPECTATOR, ticrate 35, and the exact WAD hash
`a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

The Windows host Codex app-server initialized with `gpt-5.6-luna` / `low`, but
the zero-iteration report and protocol journal show zero planner turns. The
local Docker session started MAP01, emitted three exact typed observations,
completed one observe-only submit, and reported a verified owner release with
empty `keys_down` and `buttons_down`. Three same-session host/runtime clock
probes had a 14,626,168 ns uncertainty interval; executor acceptance followed
the translated send by 60,633,974 ns. The source mount was read-only, runtime
network was disabled, and the generated report withheld evaluator score.
These outputs are a startup/release preflight only, not a formal experiment or
gameplay result. Raw preflight output is retained under `artifacts/` and at the
original local temp path recorded in `LOCAL_PREFLIGHT.md`.

Three distinct preflight attempts stopped before model inference/gameplay:
the first exposed a stale macOS Codex executable path; the second exposed an
invalid MCP override assembled by the inherited adapter; the third found the
missing `openpyxl` dependency before runtime startup. Each attempt used a
separate local output directory and was not retried in place. The adapter now
uses the Windows executable and a valid empty MCP configuration; the image
includes pinned `openpyxl==3.1.5`. These failures and fixes are preserved in
`LOCAL_PREFLIGHT.md`.

The local image is relatively large at 1.14 GB, mainly due to CPU software GL
and Mesa/LLVM dependencies. It is kept local and is not pushed to GitHub. A
size reduction is desirable only if it retains the verified no-GPU runtime.
**No #4544 formal seed/output was reserved or consumed**; the zero-decision
preflight's seed 990644 is not a formal allocation.

The Git whitespace check reports two end-of-file blank lines in generated raw
artifacts (`artifacts/effective_controller.py` and
`artifacts/preflight-zero-model-v4/runtime/doom.ini`). They are preserved
byte-for-byte as execution evidence; they are not source formatting changes.

## Limits

This work does not reproduce or explain the consumed #4536 failure. The later
main-branch #4552 audit established that the merged basic helper accepts
additional receipt fields, so no exact-key rejection cause is claimed here.

The hard-invalidation time is synthetic because #4536 did not persist its raw
receipt. This result tests the monitor contract and deterministic converter
only; it is not retrospective causal proof, adapter integration evidence,
MAP01 progress, or a gameplay result. Keep #4544 open until its full frozen
formal gate is either completed or explicitly STOPped/HOLDed with artifacts.
