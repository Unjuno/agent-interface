# PRE-MEASUREMENT FREEZE

Task `X11-MAP01-PULSE-DWELL-FIDELITY-20260917-001`, Issue #651.
Publication BASE `5d85577dd3556725bfddf6a88e379e783a13ead0`.
Formal allocation `x11-map01-pulse-dwell-fidelity-20260917-a1`.

Scientific program is exactly six XTEST `Right` press/release pulses, nominal 190 ms hold and 10 ms inter-pulse settle, in 12 fresh private Xvfb/Tk sessions. First outcomes only; no replacement/rerun/extension.

PASS requires 12/12 structural integrity, 72/72 pulse X-event dwells within [180,230] ms, and 72/72 absolute differences between X-event dwell and controller synchronized press→release interval <=5.0 ms. Final relevant X11 key state must be empty in every case.

Excluded construction and setup failures are not pooled. The explored one×1140 ms long hold produced Tk/X11 autorepeat and is not a formal comparator.
