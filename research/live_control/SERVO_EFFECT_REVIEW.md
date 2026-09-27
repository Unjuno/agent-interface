# Program, visual goal and saved effect — corpus review

The preserved corpus contains contradictions in both directions. A completed
program with a local visual goal can fail the saved task; a stopped controller can
already have achieved the scored geometry. Recovery must inspect effect evidence
before deciding whether another movement is needed.

`review_servo_effect_corpus_v1.py` reconstructs an offline review from eight existing
backend-event trials and their saved SVGs. It checks the recorded source manifests,
feedback/terminal copies, release state for admitted servos, and 59 exact PNG/AIT
frame pairs. It recomputes target displacement from SVG at the declared 118% zoom
and checks the fixture rectangle geometry. Original experiments remain unchanged.

| Preserved case | Program | Visual conclusion | Saved geometry |
|---|---|---|---|
| occlusion-02 normal | completed | goal reached | pass, +24 px |
| occlusion-02 partial | needs decision | ambiguous | fail, 0 px |
| occlusion-02 hidden | needs decision | lost | fail, 0 px |
| occlusion-02 replacement | completed | goal reached | **fail, 0 px** |
| distractor-02 blue | needs decision | lost | **pass, +12 px** |
| distractor-02 red | needs decision | update limit | fail, -48 px |
| distractor-03 blue | needs decision | lost | fail, 0 px |
| distractor-03 red | rejected | not evaluated | fail, 0 px; no admission |

The review exposes program status, local visual status, release evidence and saved
effect separately. Both contradictory cases require detail review. The rejected
case does not acquire a fabricated release record: its evidence is no servo
admission, with the validation rejection recorded in the original result file.
The blue geometry pass does not erase the controller's tracking failure.

## Implications for the live interface

The existing successful-servo card explicitly says task success is unknown. Keep
that property. A compact normal-control card must never become task-completion
evidence merely because tracking is matched, the local goal is reached, or input
was successfully released. Conversely, a needs-decision terminal must not by itself
trigger another displacement. Recovery needs a fresh observation and a separate
task-effect check where available; that check may show that no new movement is
needed. Historical review grants no new input authority.

These old experiments contain backend events, not the current caller's bound
clock/submit/exchange reports. They therefore **do not test live compact-card
fallback**. No synthetic transport envelope was added to make that test pass.
The review is a separate offline corpus artifact, not an adapter accepted by the
current live receipt path. Integrating the three statuses into live effect review,
then testing replacement and post-goal tracking loss through the actual caller,
remains necessary. Session21's known identity failure is not repaired or promoted.

## Reproduction and limits

From Linux at the repository root, choose an unused output path:

```sh
python3 research/live_control/review_servo_effect_corpus_v1.py --out /tmp/servo-effect-review-new.json
```

The committed output is `results/servo-effect-review-01/report.json`; exclusive
creation prevents accidental replacement. It includes hashes for the reviewer,
original event/result/SVG files and experiment source manifests.

This is a known-case offline review, not a fresh GUI trial or held-out validation.
Scoring covers declared displacement and rectangle geometry, not arbitrary SVG
content, styling, visual identity or full document equivalence. Source manifests
are not exhaustive environment inventories. No latency, token, cost, human-speed
or Research Freeze conclusion follows. The sources and old failures are retained.
