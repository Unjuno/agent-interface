# Issue #5970 T2 — prospective trace instrumentation

This additive experiment tests whether an isolated X11/Tk fixture can retain explicit causal provenance across two independently recorded streams. It uses the archived #4135 observer and app source as frozen inputs, then runs instrumented copies under a fresh Xvfb display. The serialized arm/ack handshake is part of the measured protocol.

The first candidate STOPped on an archive inventory predicate; the successor STOPped before input because it polled the wrong Tk log path. The corrected third candidate dispatched one Shift press after both streams acknowledged. Tk recorded the event and explicit actuation parent; the observer recorded its arm acknowledgement but no matching event. The candidate failed closed, did not dispatch the release, and returned `HOLD_INCOMPLETE_OR_NONNEUTRAL`. An independent raw-stream audit passed this HOLD adjudication. See `REPORT.md` and `RUN.md` for all attempts, limitations, and hashes.

This is a controlled instrumentation-feasibility result only. It does not change or re-run #4135's formal allocation, infer causal edges from historical timestamps, establish arbitrary distributed snapshot correctness, grant action authority, or demonstrate production recovery benefit.

Important method limit: the archived #4135 `app.py` and `observer.py` were hash-verified as reference inputs, but T2c executed purpose-built instrumented test copies modeled on their Tk/Xlib structure; it did not mechanically patch and execute those exact archived files. See `METHOD_DEVIATION.md`. No transfer to #4135's original observer is claimed.
