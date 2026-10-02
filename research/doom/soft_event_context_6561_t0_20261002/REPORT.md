# Issue #6561 host construction prototype

Status: `CONSTRUCTION_HOST_PASS_SCOPED`; formal WSLc construction and candidate/auditor allocation NOT RUN.

## Frozen source references

- Current main at final host construction: `648be0cb805a4cf44b9d8f6e1ad2a793b83bbf9a`
- v30 controller blob: `201e580e58ee7e5455a25da55bdd4e0bfb9f8a92`
- typed guard/monitor blob: `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`
- retained v30 audit blob: `980acfca962e3cc4ff8c32968692374ea0b60191`

The three target blobs were read again after main advanced from `ad6bf3f1...` to `648be0c...`; their identities were unchanged. The source module records these pins.

## Host construction test

Command: `python -m unittest -v test_research_soft_event_context_6561.py`

Runtime: Windows host CPython 3.11.9. Result: 8 tests passed.

The finite fixture covers explicit `NONE`, one and multiple observed soft events, hard/unknown/expired state, current/future sequence rejection, cross-binding rejection, no authority/success bits, and an independently recomputed latest-event/count check over retained raw events. A mutation replacing the newest soft event with an older event is rejected. An initial construction run found candidate/auditor disagreement in the reason code for nonprior events; the construction prototype was aligned and the full suite then passed. That correction occurred before any formal allocation.

## Limits

This host suite validates only the local contract prototype against authored fixture rows. Candidate and derivation functions were exercised in one host process; this is **not** the separately invoked raw-only auditor required by the frozen formal gate. It does not execute current controller code, WSLc, a container, GUI/Xvfb, game, model, GPU, or any task input. No live MAP01 result or planner-quality benefit is claimed. The previous v28/v30/v27 results remain unchanged, and #59 remains open.

Next allowed step: after a fresh source/main/readback and explicit compatible WSLc CPU lane assignment, package a separate candidate and raw-only auditor process, freeze exact hashes and gates, then perform only the assigned bounded construction allocation. No candidate/live MAP01 allocation is requested or implied here.

