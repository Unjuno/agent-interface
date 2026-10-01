# Calc modal transfer of the integrated final-action response

Disposition: **PASS_CALC_FINAL_ACTION_SCOPED** for saved effect, explicit modal
decision, request reduction and cleanup. Final painting coherence remains open.
No production code changed in this transfer; it uses the integrated main path.

The primary assistant viewed a fresh seed991103 Calc sheet with A1 selected and
public goals A1=551/A2=768, then used keyboard-only entry and Save, with the same
2ms text policy as `native-calc-explicit-task-01/run-2`. The first reply returned
a fresh Confirm File Format dialog at source sequence4. The assistant viewed the
image and explicitly chose Use Excel 2007-365 at (750,463). Only that final click
carried finish_after=true. No dialog was auto-confirmed and no input was retried.

The second reply included the action, last reviewed image, independent workbook
score [551,768] and completed cleanup. A separate workbook read confirms B1 is
empty. Both programs completed with verified neutral release; program emissions
were20 and3. The owner handle43986 subsequently exited0. Tracked application
return codes include LibreOffice255 during teardown; completed cleanup means
terminal tracked processes, not normal application shutdown or all descendants.

**Preserved image/feedback limitation:** after clicking, feedback against the old
dialog window returned needs_review/BadWindow because it disappeared. Existing
window review rebound to the main Calc window. Its capture still visibly contains
dialog pixels, although the later saved workbook is correct. This image is not
claimed to show a fully repainted final worksheet. The raw error, image, capture
identity and successful score are retained together; neither overwrites the other.

The prior same-seed task used three requests (entry, modal confirmation, finish).
This use has two (entry, explicitly final modal confirmation). The first decision
matches the old one; the second differs only in its exact presented source
sequence and finish_after=true. Local exchange intervals were approximately578ms
and726ms, excluding model deliberation and host tool overhead. No causal speed,
token, generalized modal handling or human-tempo benefit is established.

The independently structured `audit.py` reads the workbook, checks action modes,
program emissions, release, one-to-one request/reply digests, native image hashes,
pre-use source freeze and cleanup; it also rejects corrupt request links. The
historical three-request run and earlier failure remain unchanged. PLAN.md was
written before this allocation. Exact main commit and source hashes are in
SOURCE_FREEZE.json. No sensor lane, helper model or Docker restart was involved.

```sh
python3 runtime/results/native-calc-final-action-01/audit.py
```
