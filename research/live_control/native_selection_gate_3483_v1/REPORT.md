# Selection-gated save: Inkscape container allocation 991131

**Disposition:** `PASS_SELECTION_GATED_SAVED_MOVE_SCOPED` — one pinned private Inkscape fixture only. This is not a broad GUI, cross-app, production-readiness, latency, cost, or human-tempo result.

## H / T

**Hypothesis.** A source-bound click followed by inspection of a fresh linked image can establish that the same rectangle is selected; only then should a bounded keyboard movement and explicit save be sent.

**Test.** One OrbStack/arm64 allocation, seed 991131, source commit `81051d732b0180d7762bb2fd4eca6fcd57d2a99c`, image `sha256:edadb620ecb19dfd8dc5b020e4e134b68188e2bf3902e7d15ae50af55e1af46f`, network disabled, private Xvfb/Openbox, source read-only, retained interactive PTY, max two action stages. Stage 1 clicked [604,389] only. The exact linked image was inspected and showed selection handles around the red rectangle, the rectangle-selected status, and toolbar X=50/Y=50/W=40/H=30. Stage 2 then sent six Right chords, a 50 ms settle, and Ctrl+S, followed by explicit finish.

## D — result

Both requests match their source sequence and reply digest. The click used 3 emissions; the second stage used 19 total emissions (16 program emissions); each completed and each release verified empty. Feedback matched after save. The returned image visibly shows X=62 and “Document saved.” An independent XML parse confirms saved SVG `x=62, y=50, width=40, height=30, transform=null`; evaluator success is true. Raw cleanup owner/descendant flags remain false; independently, owner exit 0, terminal tracked processes, stopped unprivileged private PID namespace, and outer container exit 0 establish process termination for this isolated run.

## C — confounds and scope

The test does not isolate the causal contribution of the selection gate from the explicit settle/save tail. It combines the evidence-backed sequence: #3478 showed on-screen X=62 but disk x=50 without save; #3473 tested a settle/save suffix without an intermediate visible-selection gate; this allocation combines both. One deterministic fixture and one app cannot support general reliability or efficiency claims.

## U — unresolved

Cross-app transfer, broad target robustness, source identity at native input admission, user-task acceptance, matched efficiency benefit, and wider cleanup semantics remain open in the repository roadmap. Raw cleanup booleans also remain false despite the independent scoped termination check.

## Evidence and reproduction

The complete 62-file raw allocation bundle, exact PNGs, requests/replies, action/release records, saved SVG, cleanup records, and hashes are included alongside this report. `audit.py` is read-only and recomputes request/reply/source links, SVG geometry, releases, owner/process termination, and container lifecycle. The archive is organized so a successor can inspect the evidence without altering prior issue artifacts.

GitHub record: Issue [#3483](https://github.com/Unjuno/agent-interface/issues/3483) (closed, scoped outcome); preceding negative control [#3478](https://github.com/Unjuno/agent-interface/issues/3478); separate settle/save lane [#3473](https://github.com/Unjuno/agent-interface/issues/3473).
