# Current-main WSLc global repeat-off caller diagnostic R08

Status: **DIAGNOSTIC / OLD TASK FAILED / PRODUCT HOLD**.

Both trials set and read back global auto-repeat off (`global_auto_repeat=0`) in the private Xvfb before the standard caller. Normal mode's unittest exited 0; owner disconnect and the release worker completed (524.30 ms) with a neutral independent readback. The old task effect count nevertheless increased 1→5 and its independent oracle failed; the late-A event flag was true. A fresh-generation task passed without old-input contamination while the old fence remained UNKNOWN. Optimized mode failed the caller assertion after XRes disconnect; the unchanged 1.5 s release worker timed out, A was down at readback, and final fixture cleanup read all keys up.

The global repeat-off setting did not eliminate repeated A effects in this caller harness. This one pair cannot establish why counts differ from prior runs or whether timing caused the count; see R10/R11 direct server controls. No production setting or source changed.