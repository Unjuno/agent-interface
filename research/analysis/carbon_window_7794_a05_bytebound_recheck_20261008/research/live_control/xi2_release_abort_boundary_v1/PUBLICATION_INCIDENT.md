# Postmeasurement publication incident

During result publication, an erroneous contents-API write created a three-line placeholder RESULT.md on the owned research branch in commit `73cb80a0a261f863d6c09b0747cb082333b11000`, instead of advancing the branch to the already assembled result commit `c709239c3cd87a93da938a5f6d68f7bbf78aa49b`.

Comparison against the source-freeze commit verified that the erroneous commit added only that placeholder report. No frozen source, result, image, receiver log or shared path was modified. The complete intended result tree `30da3df5bb6c7b79a07d6c21f52a7d47f56ffb0e` had already been constructed and its report/reconstructor blobs verified against local bytes before the mistaken write.

Recovery retains the erroneous commit in history and installs the previously verified result tree plus this incident note through a normal descendant commit. No force push, history deletion, source change, new measurement, same-ID rerun or changed scientific interpretation is involved. The experiment remains STOPPED_CONTROL_FAILURE and its frozen audit remains FAIL_INTEGRITY_OR_CONTROL.
