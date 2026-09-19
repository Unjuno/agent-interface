# Retain known critical visual events across latest-image replacement

`async_events.py` adds an in-session pending-signal store to latest-observation
delivery. After each decoded observation, `signals.py` checks fixture-specific
pixel conditions: a yellow patch, disappearance of the red target, or absence
of the green player. A detected condition emits `critical_signal` with the exact
image/sequence, then exits the method with `needs_decision` and verified release.
The detection notification precedes release verification; only the terminal
event asserts that keys were released.

Pending signals survive replacement of the latest image and appear in `poll`
responses until `ack_signal` names their identifier. New input programs are
rejected while signals are pending; observation-only programs remain available.
Acknowledgement clears a notification, not the underlying visual condition,
and does not resume a discarded program. State is in memory for this session,
with events archived on disk; no crash-recovery or distributed delivery claim.

## Actual assistant use

`results/events-assistant-01`, seed 880101:

1. The assistant inspected the initial screen and started tracking.
2. A yellow patch appeared for approximately 0.5 seconds. The method detected
   it, emitted image 020, stopped before its trailing key step and verified
   release. The assistant inspected that warning image.
3. An unacknowledged input request was rejected. An observation-only request
   produced image 021, where the warning was gone.
4. The assistant inspected the clear image and polled. The old warning/image
   remained pending alongside the new image. Explicit acknowledgement cleared it.

All 21 images decoded exactly. Detection-to-verified-release was 7.99 ms in this
one trial. This excludes time from visual onset to detection and all planner
reaction time. The app continued running after local execution stopped.

## Fresh functional probes

`results/events-fresh-01` freezes the new source bytes before six fresh probes:
seeds 880201/880202, each with a yellow alert, transient target loss, and no event.
The known events occur at fixture time 1–1.5 seconds in a three-second episode.
These are scripted functional probes, not an efficacy comparison.

- All six passed; 191 packet/image reconstructions matched exactly.
- Both alerts and both target-loss cases emitted one appropriate signal,
  stopped trailing execution and verified release.
- After the event disappeared, a clear newer image did not clear the pending
  signal. New input before acknowledgement and an incorrect signal ID were
  rejected. Correct acknowledgement removed the pending signal.
- Both no-event cases completed the method and reached their explicit decision
  boundary without a critical signal.
- Detection-to-release ranged from 3.35 to 6.29 ms across four event cases. This
  is neither event-onset detection latency nor a scheduling guarantee.

The probe verifies signal labels against the pixels in their archived images,
not the configured event name alone. All underlying application trajectories
are retained after input has ended. Per-case results are in `probe.json`, the
cohort in `summary.json`, and source snapshots/hashes in the cohort directory.

## Scope and remaining limitations

These fixed color conditions are not generic warning or object recognition.
Two no-event runs do not establish a general false-positive rate. Events
shorter than the capture interval, between samples, hidden by occlusion, or
outside the detector's vocabulary may be missed. Repainting can also produce
partial frames; this experiment does not establish resistance to that case.
Images are not captured continuously while idle. Acknowledging an unresolved
condition does not itself validate the next action. Focus drift, external input,
backpressure and blocking I/O remain unresolved runtime limitations.

This adds a way to preserve **detected** events while omitting routine output.
It does not prove that latest-only delivery preserves all important information,
reduce measured model tokens, demonstrate human speed, or establish DOOM skill.
The next transfer target is the planned DOOM environment, rather than indefinite
tuning on this arena.

## Run

```sh
python3 async_events.py --out ../../results-local/event-live --seed 880301 --seconds 8 --event alert
python3 probe_events.py --out ../../results-local/event-probes
```

After the initial observation, submit the same bounded tracking program used
by `async_session_v2.py`. Use the actual received signal ID for acknowledgement:

```json
{"op":"poll"}
{"op":"ack_signal","signal_id":"track:20"}
```

That identifier is an example from the recorded assistant trial. Choose new
output paths and use identifiers/sequences from the current session.
