# Bounded Inkscape transfer admission

Source df2e5c6f3ca7288f5a054195f8a746d1ab4ead54; same primary assistant, current
public Python owner dispatch, Inkscape 1.2.2 in fresh Ubuntu Xvfb/Openbox.
One allocation only, no retry/repair or subagents, at most 10 explicit commands,
15-minute owner lifetime. Task: draw two distinct non-overlapping positive
rectangles inside an initially empty 400x240 SVG page and save it.

Retain the existing strong public-batch semantics: rectangle tool, two complete
pointer drags, explicit bounded waits, observe and release in one program; save
only after primary visual review in a separate program. Coordinates come from
this allocation's exact image, not the historical baseline. An optional explicit
page zoom with observation is allowed before choosing points. Full screen-region
capture is [0,0,1000,700]. One fresh read-only observation after ambiguous paint
is allowed; insufficient image grounding otherwise stops without input/replay.
Leases are explicit fresh caller-authored 2-second deadlines, never renewed by
owner. Same-owner cleanup always retained. Independent SVG scoring is performed
only after all owned processes are terminal: exactly two positive axis-aligned
untransformed rectangles inside page, non-overlapping.

This is transfer/use admission for the newly shared owner entry, not a matched
transport/default-wait/model performance comparison. Historical source/build,
lease, task seeds and model context differ. Preserve failed evidence as failed.
No model tokens/cost, useful-feedback or semantic-completion benefit is inferred.
