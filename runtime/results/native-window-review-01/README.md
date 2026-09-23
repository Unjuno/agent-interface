# Initial same-connection window review

This is the first retained Calc use of explicit window review on one native
bridge connection. It independently saved [116,476], returned new review images
for the dialog and parent window, and refused both old target aliases with zero
input. The next stage reused each returned review image exactly.

This implementation rotated private handle scopes and invalidated old sources,
but still used binding revision 0. It is superseded by the separately executed
[revision-aware successor](../native-window-review-02/README.md). Source snapshots,
raw results, fifteen focused test results and 60 manifest files remain unchanged.
The manifest excludes itself and this README. Fourteen native PNG/hash links
were verified. The initial success is not evidence for the later revision update.
