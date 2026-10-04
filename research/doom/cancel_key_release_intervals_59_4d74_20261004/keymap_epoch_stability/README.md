# Keycode identity across synthetic keymap changes

**H — Hypothesis.** Once the owner resolves a symbol to a keycode and admits it, changing the synthetic mapping before cancellation must not change the code used for its release. Admission keycodes and XSync-bounded release intervals should still join by physical code.

**T — Test.** A fake-Xlib probe executes the pinned input-owner source with an in-memory `keycode=code` admission-field mutation. It remaps W after both admissions in one arm and remaps W/A before the second admission in the other, then cancels and compares receipt identities.

**D — Result.** Both arms pass with verified-empty cleanup. Remapping W after admission preserves `[87, 65]` admission/release identities; remapping before the second admission yields `[87, 77]` on both sides. This supports the narrow conclusion that the owner's stored keycodes preserve the physical admission-to-release join across a later symbol-map change.

**C — Competing interpretation.** The mapping epoch remains necessary to interpret symbol meaning. The probe shows keycode continuity, not that a remapped symbol still means the same game action. Duplicate symbols resolving to one physical key remain grouped.

**U — Limits.** Synthetic Xlib only. No real X server, physical input, application/game effect, model, or session recovery was tested. The #59 live lane remains unassigned.

`probe.py`, `RESULT.json`, and `audit.py` retain the frozen source identity and reproducible result.
