# Astra MAP01 failure triage v1 — post hoc video and runtime join

## H / T / D / C / U

- **H:** The retained Astra attempt combined long model waits with a fixed, nonrenewing ten-second local cover. When enemies became visible, one firing/strafe cover overlapped an 11.741 s model call. Across the surrounding decision window it spent 11 rounds while sampled health fell 100→84; the evidence does not locate that health loss before or after the returned answer. Later fresh model answers repeatedly selected navigation while health continued to fall, and the player died without reaching the exit.
- **T:** Read the frozen `map01-astra-attempt-v1` report and 852-row runtime event log, the existing hash-checked decision frames and `failure-analysis-v1.json`, plus the complete labelled 2x video. Review the full video on two-live-second samples and the first combat interval on one-live-second samples. Bind this note to the retained media/raw hashes below.
- **D:** Separate direct observations from window-level associations. Report model wait and local-cover gaps, sampled threat visibility, HUD health/ammo, fresh-plan identity, contingency outcomes, visible navigation, and terminal score. Do not infer enemy absence off-screen or causality from adjacent-frame changes.
- **C:** Post hoc review of one frozen run only. It adds no model, GUI, game, or input allocation and does not replay or alter the attempt.
- **U:** Video samples do not identify off-screen enemies, exact damage source, projectile hits, or full-frame threat onset. HUD values are decision-frame transcriptions; health/ammo changes between decisions are window-level associations that include inference cover and the following primary program. No counterfactual survival, policy efficacy, task-effect, or MAP01-clear claim follows.

## Reconstructed diagnosis

The player progressed through the start corridor and opened the AGM door before the first clear enemy view across the lower area at the decision-3 observation (live time about 36 s). The decision-3 primary advanced and fired; ammo changed from 50 to 48. During the next model wait, `cover-4` alternated left/right strafe with fire. That model call took 11.741 s against a ten-second cover. Across the surrounding decision window the cover spent 11 additional rounds and the next decision frame showed health 84, down from 100. These adjacent-frame changes cannot establish how much damage occurred during the cover versus the following primary command.

The following fresh answer identified damage and a stair route and selected right/forward movement. The sampled video shows a nearby enemy in the lower channel during that interval. The later decision frames show the player turned into a close wall/ledge and remained there while health fell through 53 and 49. After the view returned to the open lower area, an enemy was visible approaching; the controller continued left/forward navigation at 22% and 11% health while ammo stayed at 37. No later primary command fired. The final observation showed a close enemy and 0% health; the independently scored terminal was one kill, one death, no MAP01 exit.

The original timing reconstruction remains the quantitative control result: seven of 13 model waits outlasted their fixed local cover, totaling 9.771 s of uncovered model tails, with a 3.765 s maximum. The largest late damage intervals therefore coincide with coast-cover windows, but each interval also contains the next primary action. The raw event log and video show no model-call or cover renewal in this run.

This is not a stale cached-model-answer failure: decisions use increasing observation sequences and distinct source-image hashes (for example, sequences 408 and 450 have different image hashes). It is a delayed-reaction failure: cover-4 repeats its preplanned fire/strafe cycle without responding to changing health while inference is pending, then fresh answers spend later turns on repeated route-finding while health is critical. Despite an approaching on-screen enemy and 37 displayed ammo, those later primary answers do not fire. The trace records eight authored no-visible-effect contingencies and zero activated branches, so no local contingency recovery was observed. Repeated fresh actions are evidence of weak useful reaction, not proof that the model reused stale input.

## Evidence and reproduction

- Frozen run: [`MAP01_ASTRA_ATTEMPT_V1.md`](MAP01_ASTRA_ATTEMPT_V1.md)
- Existing quantitative reconstruction: `results/map01-astra-attempt-v1/failure-analysis-v1.json`
- Full labelled video: `results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4`
- Runtime events and model/HUD report: `results/map01-astra-attempt-v1/events.jsonl`, `report.json`
- Video SHA-256: `201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4`
- Runtime events SHA-256: `e4aea04390c32ddf7d584cf3d69e0fec781c1964815a0a1ecf19663122925564`
- Report SHA-256: `586330c491798b5d9f63424ce151cd36a52e3abce75b73ba805d3748cc63f894`
- Existing failure-analysis SHA-256: `b5383b9407198cd88e9aec712018965a27081701812619e9aeb84ba3e042e1ca`
- Source tree reviewed: `b347d6f1ede81f6980932f2d7cba6d4758bf49c9`.

The video overlay records original game time while the clip plays at 2x. Recreate a full two-live-second review sheet and a one-live-second combat sheet from the repository root with:

```sh
ffmpeg -hide_banner -loglevel error -i research/doom/results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4 -vf 'fps=1,scale=320:280,tile=4x20' -frames:v 1 /tmp/astra-full-video-review.png
ffmpeg -hide_banner -loglevel error -ss 18 -to 39 -i research/doom/results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4 -vf 'fps=2,scale=320:280,tile=4x11' -frames:v 1 /tmp/astra-combat-video-review.png
```

The next live test should start from a fresh main freeze and include a threat that appears during a long model wait. It must test whether current visible HUD/frame evidence can stop or switch an inappropriate cover before the model returns, while retaining per-key release, independent useful feedback, bounded recovery, ammo, progress, and terminal evidence. No live lane is assigned by this retrospective analysis.
