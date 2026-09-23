# #1429 T1 main-thread transition-delivery harness successor

Predecessor #1426 retained `STOP_XIMAGE_NORMALIZATION_INSUFFICIENT`, scientific NONE, after completing score/terminal/cleanup but retaining zero state transitions.

One factor only: due fixture state transitions are applied by the Tk-owning main loop instead of invoking `root.after()` from a worker thread. Nominal transition offsets, actual timestamp retention, process isolation, XImage normalization, exact selector, controller/scorer, frontier schedule, sample cadence and XTEST semantics are unchanged.

Construction: exactly one ACTIVATE18 matched pair / two fresh child processes after source-first freeze/readback and #60 finite lease. First outcome retained; reruns/replacements/tuning0. Formal0.
