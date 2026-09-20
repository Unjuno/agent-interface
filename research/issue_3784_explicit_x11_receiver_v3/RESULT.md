# Issue #3796 formal-03 result

## Disposition: PASS — scoped German formula delivery

The frozen runner completed the construction gate and all four formal rows in the pinned no-network Docker image. In construction, the DE server accepted `setxkbmap -layout de` while the explicit InputOnly receiver remained connected; query, xkbcomp server dump and fresh Xlib core map changed to German. A separate US construction control remained unchanged. Both construction receivers passed focus and XTEST/XLookupString controls.

In formal rows, three fresh German Xvfb servers confirmed active German query, changed server dump and changed fresh-client core map. The independent US row confirmed US remained active and its map did not change. The frozen candidate refused trailing `€` before any XTEST events/emissions, then delivered exact `=B2*A2` once. All planned press/release traces matched: 20 XTEST emissions/events per DE row and 18 for the US control. Every Xvfb was reaped and release state was verified empty.

The independent audit ran in a second no-network container with evidence/source read-only and separate audit output. It reported `PASS_AUDIT_CONFIRMED_DELIVERY`, errors/stops/fails all empty.

## Evidence identifiers

- Formal raw SHA-256: `93aa8e30d6089aa2cb013d2dc7c3a0b93bf33ac138bfd9b324ebc0c038c6ca95`
- Independent audit SHA-256: `6b3c813668598c9b5f63c05a5ab4576bf8b387865426a46ce1fd21f996f01e90`
- Frozen runner SHA-256: `2d43c9eca291171007525c24bd9830c77b539f53782ccba42a96eb9deca82532`
- Source manifest SHA-256: `44c5b93c95b89e8425e68cdfcef6d51af42a15cf83cfba277fbc14b70ca178bb`
- Candidate backend blob: `9cae101a219348077668c8fc086acf8e13154afe`
- 25 raw-listed artifacts; 26 files including raw.json.

## Scope limit

This establishes delivery for the exact backend, pinned image, Xvfb and standard German two-level XKB, using the combined `-noreset` plus connected explicit receiver setup. It does not isolate which of those conditions prevents reset. It does not establish Calc/task effect, physical German keyboard behavior, Compose/IME/dead keys/level-3, other layouts/backends, performance, or product success. The earlier #3784/#3791 STOP records remain unchanged and visible.
