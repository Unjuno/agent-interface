# A03 exception path reassessment after A05

A03's frozen `probe.py` takes one event from `pending_events()` and immediately evaluates `int(event.detail)` in `collect_one()` before it appends the edge receipt. The raw A03 trace records `AttributeError('detail')` and an empty `edges` list. Therefore the exception occurred before a receipt was stored; it says nothing by itself about event delivery.

In the matched A05 synthetic fixture, the pre-select event queue for the down edge contained, in order, two `MappingNotify` events whose serialized `detail` was null, followed by the expected `KeyPress`. The frozen A03 collector would attempt to read `.detail` from the first returned event. This supplies a concrete, same-version/same-fixture mechanism that can produce the exact A03 exception before the key event is reached.

This is strong support for the measurement-bug hypothesis, not direct proof of A03's exact queue contents. A03 did not save event class/type or queue contents, so the offending object cannot be identified retrospectively. A05 confirms that the target key event can already be prefetched while the socket is unreadable, but does not reproduce A03's consumed execution. Preserve the distinction: likely cause supported; exact cause unverified.
