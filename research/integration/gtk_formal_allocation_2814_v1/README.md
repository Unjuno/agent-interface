# GTK formal allocation result (#2814)

One bounded local Docker allocation completed all eight cases using the
source-bundle runner, the GTK fixture image plus `python3-xlib`, and the
combined Python path `/workspace:/usr/lib/python3/dist-packages`.

Observed gates: fixed receipt order passed; useful/unavailable/guarded/no-effect/
partial/stale cases classified ready; ambiguous delivery correctly remained
unknown without replay; terminal cleanup failure remained non-ready; and the
runner scorer matched the expected disposition sequence.

This is a successful matrix receipt-emission preflight, not formal #2606
acceptance. The raw Docker log stays local; this compact record is the
reproducible GitHub result.

