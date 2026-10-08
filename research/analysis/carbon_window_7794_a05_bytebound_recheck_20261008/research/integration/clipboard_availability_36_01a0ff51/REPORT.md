# Result — native clipboard availability and delayed-effect boundary
One prospectively frozen candidate and separate raw-only auditor; retries0. Source2e31b5e39f77bd4fbdcce56e939614a0072459c4, public freeze95f8595310585ec7632de18633c44f8a8a8d8f9f, image18835dcb3335d1cc5367c78bf0c76a8174c522aebe0fd76ba743f509dcd4f309.
**PASS_CLIPBOARD_AVAILABILITY_BOUNDARY_SCOPED**, six recorded cells, ten specifically targeted rejoined/rehash corruptions rejected, five focused tests passed.
| Cell | Owner | Policy | Deadline result | Saved text |
|---|---|---|---|---|
| A01 | healthy | direct | REPLY | Cedar |
| A02 | healthy | read_before_input | REPLY | Cedar |
| A03 | absent | direct | REPLY | (empty) |
| A04 | absent | read_before_input | REFUSED_BEFORE_INPUT | (empty) |
| A05 | stopped | direct | UNKNOWN_PENDING_EFFECT | Cedar |
| A06 | stopped | read_before_input | REFUSED_BEFORE_INPUT | (empty) |

The stopped direct owner ID remained positive and unchanged. The .5s reply deadline expired with no textChanged in the recorded application journal prefix, while the X server confirmed all physical keys neutral. After the experiment resumed that exact owner, the already emitted single Ctrl+V produced one Cedar effect. No paste was replayed. Application key-release callbacks occurred later than physical release because consumption had blocked. Input release is therefore insufficient to infer no application effect.
Observed A05 diagnostic intervals: deadline to owner SIGCONT4.828ms, deadline to late saved-state reply22.366ms. These are this trajectory, not calibrated latency estimates, deadline optimality or worst-case bounds.

For stopped read-before-input, xclip reached the .5s read deadline, was killed and waited with exit-9; no paste key was emitted and the consumer stayed empty after owner resume. Absent direct sent one ordinary paste but saved empty; read-before-input refused absence. Both healthy controls pasted Cedar. This is a refusal on unavailable data, not recovery or task completion for negative cases.

Candidate UTC 2026-10-03T04:47:48.729470+00:00 → 2026-10-03T04:47:52.532968+00:00; client/container exit0. Auditor UTC 2026-10-03T04:48:14.466913+00:00 → 2026-10-03T04:48:15.075955+00:00; client/container exit0. Each source pin matched before/after. Candidate bytes91014 within2MiB cap. CPU/memory/pid configuration was observed from cgroups, not adversarially enforced. Every child owner/consumer/Xvfb exited0 and every recorded X-server keymap was neutral; owner cleared on cleanup.

Scope: six deliberately authored Qt5/Linux X11 cells with cooperative application journaling and a continuously responsive private X server. No actual Agent Interface runtime/model path, production promotion, native macOS/user clipboard, natural fault prevalence, privacy/security guarantee, general recovery, token or speed benefit. Focus/owner snapshots are endpoints, not continuous race proof. Exact bytes read before input do not prevent a later writer/change or guarantee arbitrary target transformations. Finite subprocess/container/attach limits are configured and partial-line regression tested; this run did not fault-test daemon failure or all watchdog tiers and establishes no hard real-time bound.

The empirical counterexample supports retaining UNKNOWN_PENDING_EFFECT after a post-input deadline, rather than calling it no-effect/unsent. Read-before-input is standard finite subprocess engineering, sufficient for the constructed unavailable-owner fault, not a new mechanism. #36/#57 and broad goal remain open. Original construction01 collector failure and successful native raw were retained and recovered without replay; construction02 uses distinct Willow and no native input. Previous #6916/#6886/#3981 allocations remain unchanged.
