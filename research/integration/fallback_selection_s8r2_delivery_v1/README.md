# Retained whole-selection fallback evidence — Issue #4386

This is the **2026-09-26 retrospective publication** of the completed
`fallback-selection-2311-20260925-s8r2-01` experiment. Its source/gates were frozen
locally on 2026-09-25T13:10:25.734698+00:00, not publicly preregistered on GitHub.
This delivery ran no new formal, GUI, task-input or model allocation.

Original scientific result: **PASS_SELECTION_OBLIGATION_SCOPED**.
Integration disposition: **research evidence only; no production promotion**.
Broad #2311/#2245/#2789 and the repository ROADMAP are not closed by this result.

REPORT.md and PLAN.md are exact historical originals. Their statements that
GitHub writes were unavailable describe the original session and are preserved,
not assertions about this later publication. All 633 original files, including
source, construction, raw records, environment, first audits and original drafts,
are restored losslessly from the twelve archive pieces. No old verdict is revised.

## What was tested

Six initial conditions, three native replacement recipes, two fresh repetitions:
36 private Xvfb/Tk application lifetimes. The target must become exactly `7` and a
separate field must remain `keep-42`. Entry and Text are two widgets in ONE Tk
stack, not two independent application domains. Eighteen construction cases are
excluded. Formal retries/replacements/post-freeze tuning: zero.

| Per 12 cases | CTRL_A | LINE_EXTENT | VERIFIED_EXTENT |
|---|---:|---:|---:|
| Exact editable whole value | 2 | 8 | 10 |
| Wrong editable whole value | 8 | 2 | 0 |
| Disabled before-input refusals | 0 | 0 | 2 |
| Disabled no-effect after input | 2 | 2 | 0 |
| Native key events | 72 | 96 | 100 |

The verified recipe inspects actual selection and permits at most one document-
extent refinement. Both refinements occurred on multiline Text. All protected
fields remained unchanged. Refusal is not task completion. The additional
cooperative telemetry and input cost preclude an equal-information or speed claim.
The exact upstream backend source is retained; its loader omits one unused core
import, while executed method bodies stay unchanged. Full public CLI/MCP/core
admission/lease behavior was not exercised.

## Read-only reproduction

Use Python 3.13 in a private working directory. No GUI dependency is needed:

```sh
python -B verify.py
python -B -m unittest -v test_unpack
```

To inspect original files without running any archived code:

```sh
python -B unpack.py /absolute/new/private/s8r2-original
```

The unpacker validates bounded sizes, archive and per-member digests, regular
files and paths before creating a fresh destination. It refuses overwrites.
The verifier runs ONLY the archived offline audit, its evidence controls and
policy units, then checks the entire original inventory remained unchanged.
Do not run the consumed live case/supervisor scripts. New deployment experiments
need separate current-path scope, provenance and authorization.

## Verified evidence and limits

Current read-only checks reproduce the original 3,302-check audit and 12 effective
corruption-control results byte-for-byte. Original policy tests: 17 passed.
Publication tests: 11 passed. See RECHECK.json and PUBLICATION_CHECK.json.
Same-author independent implementation/process is not external human review.
Repository-wide tests, CI and merge qualification are separate from these checks.

Original ZIP: 466,206 bytes, SHA256
`58869822368bf721d48e3dbceb49a4815397f5b1ab029bff073bf5b2551dc524`.
Published tar.xz: 95,988 bytes, SHA256
`029067b9a1e4bcb8a6fac3f210b33d542a06fc301091decbfea3bc75abb7cae7`.
It restores 633 files / 7,691,784 file bytes; the 632-entry original SHA256SUMS
and the manifest itself are independently bound. Checksums are integrity evidence,
not authentication. Readable policy.py is an exact copy from the original corpus.

Provided Linux x86_64/CPython3.13.5/Tk8.6.16/Python-Xlib0.15; authenticated,
TCP-disabled private Xvfb. No Docker/OrbStack image-attestation claim. Standard
bindings, bounded ASCII and no intervening edit between final check and input are
explicit assumptions. Arbitrary apps, IME, concurrent edits, model judgment,
actual tokens/latency and production support remain untested.

The concrete integration lesson is to distinguish backend operation availability
from semantic edit extent and independent final effects. This evidence can inform
a compatible adapter evaluation; it does not justify adding a generic runtime
component without a demonstrated need. The earlier incomplete #2245 study is not
rerun, filled in, or represented as fully recovered here.
