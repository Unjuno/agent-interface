# Native explicit finish-after integration

Base: 5f6052a1f (resolved full SHA recorded with the source freeze).
Prior route: AGENT_EXCHANGE.md finish_after and calc-final-drain-01.
H: explicit finish_after=true on a known last action removes the separate finish
request while returning the same action evidence, final reviewed image, independent
evaluation and cleanup report through the existing exchange/review path.
T: one fresh primary-assistant Inkscape seed 991105 run, viewed edge (600,378),
50ms wait, repeat 18 Right, 50ms wait, Save, finish_after=true. Require exactly
one request/reply, 26 native ops, neutral release, image linked to action review,
saved SVG x=86 and terminal cleanup. Then one fresh negative allocation with a
non-boolean finish_after must refuse before any input and preserve cleanup/error.
D: retain source hashes before use, raw requests/replies/images, program, saved
file, evaluation and cleanup; independently audit count/order/digests plus corrupt
final-image and reply-link controls. Existing exchange/review/cleanup tests run.
C: PASS only for this explicit native finish boundary if all above hold. A partial
action, release/cleanup failure or task failure is not promoted to task success.
No automatic repair or input retry. Infrastructure failure is STOP, other missing
evidence HOLD. Baseline is retained prior primary run with a separate finish;
compare request count, not causal latency or model quality.
U: human-tempo, token/cost/speed benefit, all apps and unknown dialog behavior.
finish_after closes the private allocation even when evaluation fails: callers
must select it only when they intend no further interaction. Default unchanged.
Sensor development and helper models excluded; Docker is not restarted.
