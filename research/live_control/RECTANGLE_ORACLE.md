# Bounded independent rectangle oracle

`rectangle_oracle.py` scores saved SVG artifacts independently of the controller.
`results/rectangle-oracle-01/contract.json` declares target ID, required horizontal
screen displacement, fixed pixels per SVG unit and tolerance. The source manifest
identifies the exact scorer and historical inputs. This is a DEVELOPMENT_KNOWN
oracle validation, not a new live run or held-out qualification.

The permitted effect is target x displacement of 12 ± 1 screen pixels at scale
1.18. All remaining supported rectangle attributes, object IDs/count/order and
viewport must remain identical after normalization. Named/hex fill equivalence is
normalized; editor namedview and allowed root identity/version metadata are excluded.

Five historical artifacts yield three successes and two missing/wrong-effect
failures. Eleven constructed negative controls yield nine supported failures
(unchanged, target/distractor color, opacity, distractor position, target width,
order, extra object and viewBox), plus two unsupported evaluations (style and
duplicate IDs). Unsupported evaluation always has success=false but is distinct
from a measured task failure. Existing runtime completion labels are not rewritten.

Scope is intentionally small: flat rectangles with unitless finite geometry,
supported fill syntax and opacity. Transforms, styles, strokes, other object types,
nonempty defs and unknown attributes are unsupported. This is a comparison of
declared fixture attributes, not a general SVG renderer or validity validator;
geometry sign and opacity range are not validated. Scale is fixture-supplied,
not inferred from the saved document. Unsaved application state, time/resource
budgets and unrestricted world collateral are outside this scorer. A complete
cross-domain task contract remains future work under Issue #12.

Reproduction: run `python3 research/live_control/probe_rectangle_oracle.py` from
a clean checkout with the output directory relocated or absent; it deliberately
refuses to overwrite the frozen cohort. No oracle data is supplied to control.
