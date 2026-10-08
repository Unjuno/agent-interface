# Issue #8549 method-only T0 A01

This packet validates a prospective notification-timing method, not a human attentional effect. It checks that the frozen first-event-demand × inter-event-gap schedule holds alert facts, source identity, salience, display duration, and the second-event deadline constant, and that a separate auditor can score known synthetic second-event responses by event, source, fact, and deadline.

The factorial has 2 demand levels × 3 gaps × 4 matched blocks = 24 schedules. Each core trial contains the same two valid facts and two alerts. Three detectability/review controls are labeled outside the factorial because their event availability differs by design. Six synthetic response classes exercise correct, wrong-event, wrong-source, wrong-fact, late, and missing scoring. They are not participant observations.

The candidate and auditor use Python standard library only. The auditor independently reconstructs schedules and response outcomes without importing the candidate. Four mutation controls challenge row completeness, deadline, salience, and source scoring.

The formal commands are recorded in `FREEZE.json`. Candidate and auditor each run at most once. The selected machine's OrbStack Docker daemon returned a containerd content-store error during read-only inventory, so this allocation uses the Issue's CPU/file-only method boundary on host CPython 3.14.5. No container was started. That runtime limitation does not turn this packet into a human study.

## Result scope

`PASS_METHOD_SCOPED` means only that this fixture's schedule/control integrity and response-scoring method were independently reconstructed and the four frozen mutations were detected. It says nothing about whether people miss alerts, whether a first alert impairs recognition of a second, optimal alert spacing, safety, or product benefit. Any human study needs a separate approved protocol, consent, recruitment, power plan, and prospective allocation.
