# Fresh modal positions with observed geometry translation

Before collecting images, probe_modal_translation.py writes a plan with two new
client origins, (440,250) and (310,350), and unchanged template/threshold config.
It moves the real Calc format modal with wmctrl and captures Excel-focused and
ODF-focused states at each position. Four images were visually inspected. The
normal dialog client origin is (386,322); measured translations are (54,-72) and
(-76,28). Client dimensions remain 507×174.

The fixed-coordinate predicate abstains on all four, including both intended
Excel states. modal_visual_predicate_v2 translates the two comparison regions by
the observed geometry delta. It accepts both Excel states and abstains on both
ODF states without changing threshold .03 or source template. Geometry is sampled
before/after capture and equality is checked; this is not an atomic snapshot.

The audit replays all four results exactly, validates source hashes, retains image
hashes, verifies old zero-offset coordinates abstain and offscreen regions return
unsupported_region. This is FRESH_VARIANT within the known locale/theme/dialog
family, not a held-out domain or blind benchmark. No scoring or action is selected
by the predicate; the setup driver collects fixtures and Escape ends the dialog.

Translation is explicit caller input derived from public X11 geometry, not a visual
search result. The predicate itself cannot authenticate offset, window identity,
freshness, active focus or scale. A caller supplying an incorrect but plausible
offset could match unrelated content. Changes in size, decoration, DPI, wording,
occlusion or copied dialogs remain unqualified. Visual candidate still carries no
authority and no semantic verification.

The result removes the tested fixed-position limitation while retaining focus-state
discrimination. Next bind these observed dependencies to any prepared branch and
revalidate at admission; do not reuse historical geometry or infer live authority
from matching pixels. No autonomous modal control or latency improvement is claimed.
