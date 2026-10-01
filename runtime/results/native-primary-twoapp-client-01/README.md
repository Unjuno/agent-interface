# Primary two-application use of the integrated host client

On merged main b3af4e85f8bf7d41da5251b1728a6ddab34c3476, the primary assistant completed one Calc/Inkscape allocation through the reusable Node host client, Python relay and native MCP. No helper model, sensor, runtime change or automatic retry was introduced. The plan was saved before the first start request: seed 991323, gap 2 ms, maximum 24 stages, one allocation. This is a fresh task instance in a familiar workflow, not an independent model generalization or matched efficiency study.

## Results and remaining friction

| Recorded item | Result |
|---|---:|
| Calc saved cells | A1=753, A2=599 |
| Inkscape saved rectangle | x=56, y=50, width=40, height=30, no transform |
| MCP calls | 11: two start/wait calls, eight stage submissions, one status |
| Input programs | 5: select, move/save, app switch, type/save, format confirmation |
| Explicit observations | 2 |
| Pre-input refusals | 0 |
| Images presented through host callbacks | 8 |
| First start send to finish presentation callback | 94.966 s |
| Sum of send-to-callback intervals through finish | 8.670 s |
| Time between those calls | 86.295 s |
| Initial useful-image callback to recorded visual-completion judgment | 82.691 s |

The assistant saw selector handles before moving the rectangle, then saw X56/Y50/W40/H30 and a saved status before switching to Calc. Alt-Tab returned a usable Calc image without another observe call. Calc's save transition returned a valid but unpainted dialog frame; an explicit observe was required. After format confirmation, a destroyed-dialog feedback error was retained while the new window review still captured stale dialog pixels; a second observe supplied the visibly completed worksheet. The primary completion note preceded the finish request and independent saved-file evaluation. No completed input was replayed.

All five input receipts report completed execution and verified empty release. Both independent application scorers succeeded, and the standalone verifier also parses the saved XLSX/SVG. This is evidence about those saved effects, not comprehensive collateral-state scoring. The owner and relay subsequently exited 0. Existing cleanup owner/descendant verification flags remain false; no full process-tree claim is added.

## What the timing establishes

The host wrapper recorded performance.now() immediately before send, after the retained response resolved, and after text/image presentation callbacks returned. These are one host's monotonic intervals. Host callback return is not proof of UI rendering time or the first useful model-visible feedback. The following tool calls recorded primary visual judgments, which provide observed checkpoints rather than exact cognition onsets.

The 94.966-second interval includes inter-call assistant reasoning, tool orchestration and commentary, but excludes module import, client creation and plan writing before the first send. The 86.295 seconds between calls cannot be labeled pure inference or pure idle time. Initial start/wait cost was 6.358 seconds; subsequent input/observe send-to-callback intervals were 0.134–0.461 seconds. Fast individual RPCs do not establish human-tempo task completion.

Provider-reported input/output/cache/reasoning token usage, model build/settings, host rendering latency, a matched baseline, human reference, comprehensive hardware/concurrency capture and cold acquisition cost are unavailable. No token saving, price, general speedup or Issue #57 completion is claimed. The result motivates measuring and reducing complete observation/decision handoffs; it does not justify a longer default wait or automatically acting on a title match. The earlier final-wait study remains HOLD_PRODUCTION_ADOPTION.

## Retention and verification

`raw.tar.gz` and `manifest.json` retain 182 files: the pre-use plan, all requests/replies, host timing and primary judgments, native action/observation records, source hashes, failures, images, saved outputs and cleanup/terminal records. The host instrumentation was entered in the primary conversation; this archive is not an executable replay of model reasoning or host rendering.

Run `python verify.py` from this directory with its four files. It checks complete byte inventory, pinned source, call identities and counts, image-block/capture hashes, input/release records, observation count, the recorded review-before-finish ordering, timing arithmetic, terminal receipts and independently parsed saved values/geometry. It never extracts or executes archived code, launches a GUI or asks a model to repeat the task. Validation of primary-review records establishes their retained ordering, not an independent proof of the assistant's visual reasoning.