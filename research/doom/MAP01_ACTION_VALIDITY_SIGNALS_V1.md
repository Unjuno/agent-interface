# MAP01 action-validity signals v1

The first fresh-action boundary could only exercise health. That signal is
useful for damage policy but cannot distinguish whether a fire action still has
ammunition. This follow-up adds exact ammo extraction and an action-specific
planner-contract adapter without changing the frozen v32 controller.

## Exact screen signal

`doom_hud_signal_v2.py` reuses the hash-bound Freedoom WAD glyph templates and
exact foreground matching from the retained health reader. It adds only the
frozen adjacent ammo anchor. It reads ammo from all247 retained v31 X11 frames
with zero unknowns. Its values at the eight independently transcribed decision
frames are exactly `48,48,47,47,46,45,45,45`; the complete transition sequence
is `48→47→46→45`.

This is screen evidence. It does not use ViZDoom labels or hidden game state.
Unsupported signals, a different anchor, WAD hash mismatch, unsupported geometry
and unavailable images fail closed.

## Action-specific contract

`doom_action_validity_contract_v1.py` converts a bounded semantic specification
into the generic fresh-action contract. Every action binds exact health with an
absolute critical minimum and maximum loss from its source. `fire`,
`advance_fire` and `retreat_fire` must also bind a positive ammo minimum from
the same observation epoch. A movement-only action must set the ammo dependency
to zero, preventing unrelated evidence from causing avoidable rejection.

The exact-frame v2 replay uses synthetic fixed specifications over the five
historically admitted v31 plans. Three fire-bearing plans receive health+ammo
predicates and two movement plans receive health predicates only. All five
remain `VALID_CURRENT`; setting current ammo to zero in a fire case yields
`REJECTED_PREDICATE`. No model or input runs.

This closes one deterministic non-health signal, not the visual target question.
Ammo availability cannot show that an enemy remains present or aligned. A brief
development check of immutable/successively updated visual patches was not
promoted: sprite animation, blood overlay and camera-relative motion make exact
patch identity the wrong contract. Feature or optical-flow tracking would need
an explicit ambiguity/loss gate and independent target ground truth. OpenCV's
[optical-flow documentation](https://docs.opencv.org/4.12.0/d4/dee/tutorial_optical_flow.html)
exposes per-point tracking status, while its documentation also cautions that a
found point alone does not establish correct identity. Do not treat tracker
output as semantic target presence without that additional evidence.

## Limits and next gate

The authored values in the replay are construction inputs, not planner outputs.
The next schema must make the planner provide the immediate-action validity
specification and the controller must bind it to the exact source signals. A
v33 integration should be model-free first and must preserve:

- zero Executor admission for missing/misaligned ammo or failed predicates;
- no added image or model boundary;
- exact validity receipt recomputation at final admission;
- `action_validity` separate from `next_cover_validity`;
- v32 source hashes and frozen live preregistration unchanged.

No safety, usefulness, latency improvement, gameplay, completion or generality
claim follows from this retained-trace construction.
