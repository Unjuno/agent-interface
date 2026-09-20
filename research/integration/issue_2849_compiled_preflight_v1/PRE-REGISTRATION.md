# H/T/D/C/U — compiled schema gate for Docker allocation v2

Date: 2026-09-21. Preregistered in Issue #2849 comment 5751318209, before this fresh request.

## H — Hypothesis

With the auxiliary-event-aware runner, the compiled grounding schema can pass one fresh no-image structured-output preflight over the selected Docker/OrbStack host IPC backend. If it fails, the six-task Docker allocation must stop before GUI/task input.

## T — Target

One compiled-schema compatibility preflight only. No image, GUI, fixture task, retry, or six-task allocation in this rung.

## D — Design

- Select the Docker backend at PR #3647 head `6a942ea04bfea1d196d19719ec59a9bdad720826`; use its broker and schema-preflight implementation. Use the additive event-accounting runner merged in main at `a08935cc6efb73322e247b519fbd9d63a7b2741f`.
- Model: gpt-5.6-luna, low. Mode `handle`, image null, empty workspace, authority false.
- OrbStack Linux/arm64, `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, network disabled, read-only root, source mounted read-only, `/tmp` on tmpfs.
- Retain one IPC request, response event stream, broker receipt, process receipt, runner classification and independent Draft 2020-12 schema audit.

## C — Constraints

Exactly one fresh model call; no retry. Historical PASS/FAIL evidence is immutable. This preflight proves only compiled endpoint/schema compatibility, not GUI/task effects, six-task integration, or a benefit claim.

## U — Update / stop policy

Any nonzero runner/CLI result, malformed or missing receipt, wrong event cardinality, missing usage, authority-bearing request, or independent schema failure is FAIL/STOP. No six-task run is authorized by a failed result. A PASS permits creation of a separate preregistration for the Docker six-task allocation; it does not silently extend this experiment.

## Duplicate and conflict check

Issues #2817, #2849 and #3489 cover the surrounding preflight chain. PR #3647 remains the selected-backend implementation branch; PR #3698's runner evidence is merged. The compiled preflight is separate from the plain-only PR #3698 scope and has a fresh request id.
