# Primary use of the extracted native guarded form method

The existing six-task native harness now calls `native_guarded_form_v1` for its
two-target enter/submit method. One new development allocation, seed 991326,
used that candidate with primary-assistant grounding and per-task image review.
No helper model was launched. The plan was saved before launch; candidate file
bytes were captured after the run. This is not an immutable-source preregistered
or matched performance comparison. Base: d5c431a61ee7c37645a632a8680d1763660caabc.

The assistant viewed sequence 2 and selected field [300,401], submit [377,401].
Tasks 1-3 reused those scoped references. On task 4, the layout change caused
MISSING before entry, with zero emissions. The method stopped before Submit.
The assistant viewed sequence 37 and explicitly repaired with field [760,558]
and submit [689,634]. Tasks 4-6 then reused the replacement references.

The assistant viewed SAVED images and recorded completion interpretations at
sequences 12,23,34,47,58,69 before final independent evaluation. The server's
append-only history contains exactly t991326-1 through t991326-6, one per task,
with no duplicate, unexpected or missing submissions. The caller's visual
reviews did not independently inspect the token value on the generic SAVED
page; exact-value correctness is established separately by this retained history.

All 12 successful method input programs have VALID target guards and verified
empty release. The initial task-4 refusal remains in tasks.json alongside the
repaired result. The method's completion does not imply semantic text-entry
verification between the two clicks. This fixed method is distinct from the
compiled GUI conditional state graph, and does not expose a new public MCP API.

Successful method intervals were 532,523,538,561,578,661 ms. These include input,
existing 100 ms waits and step persistence, but exclude navigation, grounding,
primary interpretation and repair waiting. They are not end-to-end task times
or a speedup comparison. Actual primary-model tokens/cost are unavailable.

The harness exited 0. Its tracked processes all reached terminal states, with
recorded return codes 0,1,1; this is not a whole-descendant cleanup guarantee.
Local integration checks passed 223 protocol and 97 harness tests. New controls
cover missing/unverified release, first/second input failure, retained completed
prefix, persistence failure, uncertain dispatch and invalid references before
input. Test doubles are separate from the six-task live evidence.

`raw.tar.gz` retains 316 files: exact candidate source copies, grounding inputs,
images, raw input programs/results, primary reviews, refusal/repair records,
submission history, cleanup, plan, and check logs. `manifest.json` hashes every
member. Run `python -O runtime/results/native-method-primary-01/verify.py` to
validate retained identities, image bytes, exact submissions, guards, releases,
refusal/repair, review-before-oracle order and tracked termination without replay.

This integration makes the already-used method callable outside its original
inline script. Further public CLI/MCP exposure must preserve this contract and
its limits. No generic form correctness, token saving, human-tempo performance
or completion of #57 is claimed.
