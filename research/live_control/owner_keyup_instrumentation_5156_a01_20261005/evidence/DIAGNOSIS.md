# A01 frozen run outcome

The candidate ran once in the frozen WSLc envelope and exited 0 with five cases. The independent auditor ran once and exited 1 with `FAIL`; preserve that frozen outcome. All six audit mutation controls were rejected.

The raw result shows bulk and cancellation KeyRelease calls preceding one shared XSync, a neutral final fake keymap in every case, and a failed-sync receipt with no completion timestamp followed by successful close cleanup. The audit failures are attributable to two defects in the frozen auditor: (1) its bulk/cancellation order check compared releases to the first sync in the case, which belongs to earlier key-down requests; and (2) it calculated both injected-failure sync sequence numbers from the same pre-extension list length, assigning the cleanup sync the wrong ordinal. This note is post-run diagnosis only and does not alter A01's decision or rerun either frozen command.

A02 is a separately frozen successor intended to correct these auditor defects. It must retain A01 as a failed historical rung.
