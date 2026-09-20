# Issue #3573 result — OrbStack portable MCP zipapp smoke

## Status

**PASS_PORTABLE_MCP_ORBSTACK_SCOPED.** Two isolated allocations completed the
preregistered MCP discovery, image, single-dispatch, fixture-effect, retained
receipt and input-release gates. A separate attempt to build the archive inside
the minimal runtime image stopped before any API call because `git` is absent;
the preserved note is `PREFLIGHT_STOP.md`. Runtime package construction instead
used the frozen committed source SHA below.

This result does not establish a registered desktop host, model-visible image
delivery, model task success, host-side presentation, generalized application
effect, or latency/token/cost improvement. The owned Tk fixture was reaped when
its container ended; its Python mainloop did not return a graceful zero exit
under TERM/INT. That cleanup nuance is retained, not promoted as a graceful GUI
shutdown claim.

## Frozen inputs

- Source commit: `79bd0410e7baac734be2190a9ae7200f91b5c940`.
- Zipapp SHA-256: `ed1fde53d1635960e146e4d765ab0658aef67a25c73863b399f092fd1f637140`.
- OrbStack image: `sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`, Linux/arm64.
- Runtime: Python 3.12.3, MCP 1.30.0, python-xlib 0.33, Pillow 10.2.0.
- Runtime container was network-disabled, read-only-root, with read-only artifact/source mounts and one writable evidence mount.
- Client cwd was temporary and its environment omitted both repository and `PYTHONPATH`; only the private fixture subprocess received the explicit read-only source mount.

## Formal allocations

| Allocation | MCP init | Tools | Observe | Dispatch | Saved effect | Release | Result |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `20260920-formal-01` | 1 | exactly 2 documented tools | 1 PNG image block | 1, completed + PNG | exact unique marker | verified, no keys/buttons down | scoped gates pass; fixture exits via signal at teardown |
| `20260920-formal-02` | 1 | exactly 2 documented tools | 1 PNG image block | 1, completed + PNG | exact unique marker | verified, no keys/buttons down | same scoped gates independently reproduced |

Each allocation has two MCP call directories, each with one request and report;
the dispatch report contains its retained PNG. Both effect files were read
independently of MCP presentation. Raw requests, reports, PNGs, event logs,
effect files, process logs and summaries are kept beneath `evidence/`.

## Audit / reproduction

`audit_result.py` checks the exact tool set, per-operation call counts, separate
image blocks, PNG/archive hashes, retained request/report cardinality, exact
effect marker, completed dispatch and verified release. It intentionally does
not score a model or a real desktop host. `container_smoke.py` is the one-shot
container runner; `Dockerfile` extends the pinned local OrbStack X11/MCP image
with Tk for this disposable fixture.
