# Addendum 01 — event observer resource handle

Pre-run inspection found the probe attempted to select events through a nonexistent `Display.change_attributes` method. No container/test attempt had run. The frozen probe was corrected to create a `Window` resource object on the separate observer connection and select KeyPress/KeyRelease events there. The measured XTEST sequence, delay, key-repeat setting, and decision rule are unchanged. This is a harness-only repair before the single declared diagnostic attempt.
