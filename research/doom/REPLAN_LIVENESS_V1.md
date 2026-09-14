# Replanning liveness after natural stale-cover safety

## Observed failure

V28 safely interrupted five matching high-level turns and cancelled one
nonempty stale cover under a real MAP01 threat. It also interrupted five of six
decisions while health changed repeatedly. The interface currently has a safe
stop rule but no liveness rule for sustained change.

This changes how earlier cover work should be classified. Renewable local cover
is not rejected in every condition. It is mechanically useful while the planner
is slow, and v28 shows that it can keep acting under threat. Its missing condition
is an explicit validity envelope that says which observed changes it may absorb
and which changes revoke its authority.

## Related control ideas

Brooks' layered control keeps lower competence layers operational on their own
and lets higher layers suppress them when needed. That supports a continuously
running bounded local controller beneath slower deliberation rather than making
every sensor event restart deliberation:
<https://people.csail.mit.edu/brooks/papers/AIM-864.pdf>.

Anytime Dynamic A* reuses earlier search effort and incrementally repairs a
solution when the world changes. The transferable point is to repair only the
invalid dependency rather than discard all work on every update:
<https://aaai.org/papers/icaps-05-027-anytime-dynamic-a-an-anytime-replanning-algorithm/>.

Temporal Planning while the Clock Ticks explicitly models that execution begins
after planning delay. The current interface must likewise bind a plan to the
world expected at its actual admission time:
<https://ojs.aaai.org/index.php/ICAPS/article/view/13878>.

A recent hierarchical event-driven system separates decentralized execution
from centralized deliberation and filters events for task relevance before
replanning. Its domain and evidence are different, but the event-classification
boundary matches the failure exposed here:
<https://arxiv.org/abs/2511.22354>.

Kvarnstrom, Heintz and Doherty attach global and operator-specific monitor
conditions to plans, preserve those conditions as high-level plans become
lower-level commands, and subscribe only to state needed by active monitors.
That supports making `cover_validity` part of the admitted cover contract and
activating its signal work only while that cover executes. Their UAV system is
evidence for the architecture pattern, not for this HUD extractor or threshold:
<https://cdn.aaai.org/ICAPS/2008/ICAPS08-025.pdf>.

## Candidate contract

The next candidate should keep the existing one-way authority rule and add a
typed validity envelope to a nonempty local cover:

```text
planner action
  commands
  next_cover
  cover_validity
    soft observable transitions -> record + continue bounded cover
    hard observable transitions -> cancel cover + interrupt matching turn
    lease/time bound             -> renew only while the envelope is current
```

The envelope must reference locally verifiable signals and must never authorize
a new action. A soft transition can preserve existing bounded authority; a hard
transition can only reduce it. For MAP01, a benchmark adapter could expose a
checked health/ammo signal and test an authored critical floor. The shared
interface primitive is the typed signal predicate and authority transition, not
the DOOM-specific HUD parser.

A fixed debounce is not sufficient because it delays both harmless and critical
events without distinguishing them. A fixed number of ignored pixel changes is
also weak because changed-pixel count does not encode damage magnitude. The
first candidate therefore needs a deterministic signal extractor plus explicit
soft/hard predicates before another model allocation.

## Minimum next test

Use the retained v28 trace as model-free input first. Verify that:

1. the current envelope reproduces five interrupts;
2. a proposed envelope never creates new input authority;
3. soft events keep an already admitted bounded cover and reach the planner;
4. a hard event still cancels and releases within the current safety envelope;
5. expired, missing, malformed, or binding-mismatched signals fail closed;
6. event coalescing preserves the newest exact evidence for the planner.

Only after those invariants pass should a new fixed-threat allocation compare
completed decisions, interrupt rate, stale input, release latency, damage,
survival/progress, and attributable token use. V28 remains the baseline. One
run cannot establish a general rate or survival advantage.

## Construction replay result

The model-free construction now reads a hash-bound HUD health value rather than
assigning meaning to a raw pixel delta. It reads all 70 exact v28 observations
without an unknown result and matches 19 manual review points across v28 and an
independent v23 allocation. The v28 sequence includes a 97-to-100 pickup as well
as damage, so direction is observable. Missing, malformed, expired and binding-
mismatched evidence fails closed in the generic guard tests.

With a development-only posthoc floor of 80, the replay preserves existing
authority through two distinct soft values, 87 and 81, and hard-invalidates at
79. That is 17 exact samples and 5,240.235886 ms after the old guard's first raw
change. This does not prove that the extra interval is useful: no planner runs in
the replay and the floor was chosen after seeing the trace. Integrate the typed
envelope into the controller and verify release/stale-plan invariants model-free
before freezing another live allocation. See
[the retained construction replay](MAP01_COVER_VALIDITY_REPLAY_V1.md).

V29 now attaches that condition to `next_cover` in schema v4 and binds it to a
fresh exact health signal when the cover is admitted. A source already below the
authored floor or an envelope wider than the current 20-health construction cap
admits no prior cover commands. Soft samples stay local and coalesce; hard or
uncertain evidence uses the inherited interrupt, cancel, verified-release and
stale-answer discard path. Thirty-two relevant Windows tests and the 15-test
WSL/Linux subset pass. This is still model-free construction; see
[the v29 contract](MAP01_TYPED_COVER_VALIDITY_V29.md).
