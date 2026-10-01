# Actual X11 capture-to-operation association

Source: 92a932bc5. One owned WSL Xvfb :147 allocation, no model or sensor worker.
The retained program focused the fixture (op 0), captured the full window (op 1),
captured the green crop (op 2), and released input (op 3). Public dispatch returned
completed; review returned image index 1 and recorded operation_index 2. Both
captures retain operation indices [1,2], and the selected PNG hash matches the
second capture. The runner asserted these associations against the actual
response and exited 0 after closing its client/server. No replay or extra input.

The selected crop matches the previous public-dispatch-review-01 PNG hash;
this run validates metadata association, not new model visual reasoning. It is
not a timing, task-success, token-use, sensor or general reliability experiment.
The separate partial-execution test covers capture before later input/failure.
Raw response, program, review and images are unchanged. Historical paths grant
no fresh authority. Manifest covers every file except itself.
