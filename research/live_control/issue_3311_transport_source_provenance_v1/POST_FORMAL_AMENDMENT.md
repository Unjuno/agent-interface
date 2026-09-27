# Post-formal review amendment

After the single formal invocation completed successfully, automated PR review found that `formal_runner.py` printed all reports but returned exit code 0 even if a report contained a failed semantic check. The frozen v1 audit itself correctly emits `FAIL_AUDIT`; the wrapper exit status did not enforce the preregistered all-pass decision rule.

The runner now returns nonzero unless every report has the exact expected PASS disposition and every check is true. A unit control covers a valid all-pass set, a `FAIL_AUDIT`, a false check under a PASS label, and an empty report set.

This is a correction to future failure signaling only. The formal audit was not repeated: its three retained outputs each already contain the expected PASS disposition and 18/18 true checks, and its original invocation exit code was 0. Those reports, raw evidence, and the preformal freeze remain unchanged. The 4 original preformal controls and 1 post-formal review control are listed distinctly; no post-formal experiment was run.
