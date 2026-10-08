# Prospective construction change — formal not started

The first native static construction remains STOP at checkpoint
e2fbed6ef22e091a89c5f21590eb77634c08abf0; no scientific phase cells were run.
Its sleep-only common.py SHA-256 is
a4e6efdd2bd9f605f814ea6548a2259dca8699caa8672794aa1988526c3bad66.

The separately named, excluded timer01 container executed 16 timer-only waits
in balanced sleep/coarse-spin order, no X11/model/input. Sleep maximum lateness
was 5.176022ms versus 0.055290ms for coarse-spin. Mean process CPU per wait was
0.128224ms versus 11.613718ms. cpu.stat showed zero throttled periods before
and after. These eight observations per arm do not prove the original native
failure cause or provide a scheduling guarantee.

Before formal source freeze, common.until is changed for both source and
capture processes to sleep until 15ms before deadline and spin through the
remaining interval. The scientific frame count, source windows, schedules,
10ms capture/source lateness gate, 190ms max gap, and width +/-5ms exposure
gate remain unchanged. The additional CPU cost is part of this method.
This is not a low-CPU or hard-real-time result.

One distinct static construction02 (dark and persistent, not phase-matrix
cells) must qualify the combined native path. Native01 raw and terminal STOP
are never replaced. Formal candidate/auditor counts remain 0/0 until a
prospective final source/image/gate freeze is published to issue #6067.
