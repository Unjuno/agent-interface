# A2 transport experiment, revision 2

H: exact changed tiles can reduce serialized observation bytes relative to exact
whole-frame O1 under identical zlib level 1, while preserving every sampled
pixel and task correctness. This is a transport hypothesis, not a claim of fewer
model tokens or faster end-to-end agent work.

T: four live X11 apps from frozen A1: XTerm, Chrome for Testing 145, LibreOffice
Calc and Inkscape. Same public controller, goals, reset, pacing and independent
post-controller output oracles. Inkscape now uses the shared segmented motor
feedback controller: retain 30 ms press dwell, capture while holding the button,
then capture after each 4-pixel trajectory segment before release. Every event
is logged, final public movement is still required, and there is no retry. Both
arms use identical planned input events. The actual final receiver image drives control.
The old in-process O1 observer remains shared instrumentation in both arms.
PNG/wire archival and independent audit are outside task timing. Tile size 64,
zlib level 1, exact equality, choose shorter full/tile wire packet. This policy
charges full and tile encoding work; no claim it is an optimal tile size.

D: revision 1 stopped on baseline Inkscape 750103 after 31 attempted fresh
episodes (30 successful): pixels reconstructed but the drag did not move the
object. Its entire fresh efficacy comparison is rejected, not pooled into r2.
Revision 2 development seeds 741101–741102 (2 pairs/app, 16 episodes), plus
regression of old failed seed 750103 in both arms. Correctness errors
stop the run, are retained, and require diagnosis/new revision. Unit tests cover
single-channel changes, image edges, modes, resize, dense redraw, repeats, gaps,
reordering, wrong streams, reconnect, malformed count and trailing bytes. Two
assistant-driven exploratory tasks use separate seeds 730101/730201; neither is
an efficacy sample or a model comparison. After development, freeze all local
sources plus inherited controller/oracle and versions. Fresh replicates use
770101–770104 and 780101–780104: 4 pairs/app/rep, 64 episodes total. Reverse
O1/O2 order on alternate seeds; shuffle app/seed pair order by seed. No overlapping
GUI benchmark processes. Each worker has a 90-second deadline and private session.

C: hard gate is all tasks correct and zero pixel/continuity audit failures.
Replay all archived packets through a new decoder, compare to independent raw
PNG archive, verify PNG digests and action/context/timestamp continuity. Verify
complete paired schedule, same goals/logical operations/input events, same frozen
source/version identity. Report paired live wire reduction and same-trace wire
reduction with 10,000 whole-pair bootstrap resamples, fixed analysis RNG 65537.
Report encode/decode and paired task-wall differences, plus first-feedback timing.
Small sample tails are descriptive. Any failure prohibits efficacy promotion.

U: a pass only admits this Python codec for further research and dogfooding.
It does not promote a runtime API. Output is reconstructed full images before
model viewing, so transport savings do not establish fewer image tokens. No
network latency, model reasoning time, hidden-state correctness, general apps,
Windows capture, arbitrary language typing, or long-horizon reliability claim.
Raw trusted local producer assumption; no network service is exposed.
