# #1435 T1 edge-triggered actuation successor

Predecessor #1429 exposed a retained sample->send->effect boundary race under repeated ADVANCE actuation. The exact #1378 selector remains unchanged.

One mechanism factor only: actuator emission changes from one F8 per CLEAR sample to one F8 on observed entry into CLEAR. Initial CLEAR counts as an entry. WATCH/YIELD remain no-input. Process isolation, XImage normalization, Tk-main-thread transitions, 0/40 ms frontier, 5 ms cadence, scorer and authority remain fixed.

Construction: exactly one ACTIVATE18 matched pair / two fresh child processes after source-first freeze/readback and #60 finite lease. Candidate must send exactly once, produce progress>0/harm0, useful latency<=12ms, no WATCH effect, and pass terminal/cleanup. First outcome retained; reruns/replacements/tuning0. Formal0.
