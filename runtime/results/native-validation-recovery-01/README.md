# Live refusal recovery: partial recovery, task failed

One primary-assistant WSL Inkscape session on source d05295fce, seed 991123,
max_stages 2 and text_gap_ms 0. This is integration evidence, not container
adoption, an independent review, or a latency/model-token comparison.

1. native_start returned a source image; the primary assistant viewed it.
2. A keyboard decision containing only wait_update was rejected by schema
   validation. The retained check recorded no request-1.json or harness error,
   and the same owner PID existed. No application restart occurred.
3. The primary submitted a different, valid click/move/save/finish_after decision
   at the same stage and source. Publication succeeded. The selected point
   [619,391] was inside the uniform red rectangle; target minting refused it as
   visually flat. No action program ran and no saved-task evaluation succeeded.
4. native_status confirmed the same owner exited with code 1; relay EOF exited 0.

The new early validation preserved the request slot, but this trial does not
prove end-to-end task recovery. Target-mint refusal still terminates the harness.
The primary's central-point choice is part of the failure evidence. Do not weaken
visual binding to turn this into a pass. A future integration change should
consider whether an explicitly unexecuted targeting refusal can safely return a
fresh decision boundary, with action dispatch and cleanup semantics kept explicit.

Full MCP responses, original image, request, error, cleanup records and source
files are retained. audit.py checks the recorded claims and byte hashes; it does
not rerun the GUI or classify the screenshot. Manifest excludes itself only.
