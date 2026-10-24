# R17 — fresh target-generation task effect

## Question and scope

Can a newly launched Notepad target with a generation distinct from R16 complete one exact task through the standard supervised-Win32 public MCP caller, with same-generation admission evidence, independently verified task effect, confirmed input release and bounded cleanup? This directly tests target-generation propagation across a new target window/process identity.

This is one fixture task, not a matched efficiency comparison, broad reliability estimate, model/provider run, stdio transport test, MAP01 result, or WSLc run. The comparison target is R16 generation `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`; R17 must refuse input if the selected window has that same generation.

## Frozen selection and stop gates

Record the existing Notepad window IDs, launch Notepad once through its returned app ID using Computer Use, and select only one newly returned window ID. Activate that exact returned window. Pass its returned HWND as `R17_TARGET_HWND`; do not select by title because existing windows share a title. Before any input require visible, enabled and foreground target, exactly one RichEditD2DPT child, blank text, SHIFT-up, and generation different from the R16 baseline. The public observation must preserve that generation. Any ambiguity or mismatch records a no-input STOP.

## Frozen task and evidence

Dispatch one public `text` operation for `AI-CTRL-20261024-R17` using `gap_ms=25`, bracketed by `release_all`. Poll native text during dispatch; verify the exact call against a native same-generation oracle; then use one separately verified select-all/backspace cleanup. After session close, independently verify the fresh generation, empty document and SHIFT-up. Preserve the UI selection, raw requests/reports, screenshots, timings, cleanup, postflight and manifest. Dispatch-to-observation is not physical key latency or model inference time.
