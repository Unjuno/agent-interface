# Readme — #57 unpainted-dialog handoff reconstruction A01

This is an offline, posthoc reconstruction of the existing `recovery-assistant-01` Calc trace. It isolates four adjacent images around the unpainted format dialog, recomputes PNG pixel differences and image-ready timestamp intervals, and carries forward the original audit's task and release scope. It is not a new GUI run or a formal experiment.

Run from the repository root with Python and Pillow:

```powershell
python research/integration/unpainted_dialog_handoff_reconstruction_57_a01_20261005/analyze.py
```

The script validates pinned SHA-256 values for the JSON inputs against `SHA256SUMS`, checks selected frame timestamps/focus flags, verifies the existing audit summary, computes image differences, and writes `RESULT.json`. Source trace and images remain unchanged. Hashes in `SHA256SUMS` cover the immutable input files used here.

Result: #006 has the modal window in window-list context while the image is unpainted; #007 is painted; #008 still shows the dialog after the confirmation action and its focus samples disagree; #009 shows the worksheet. Image-ready deltas are 16,034.582 ms, 7,045.820 ms, and 8,557.071 ms. Pixel changes are 11.7682%, 0.2426%, and 11.9498% respectively.

Interpretation stays narrow: the extra observation delivered a visibly useful frame in this one trajectory, but the trace cannot establish the exact onset of useful feedback, causal wait savings, component-level delay, general reliability, or a default wait/sensor policy. Original audit reports 9 exact frames, 4 completed programs, successful saved values `[222, 440]`, verified releases, and owner shutdown with release.
