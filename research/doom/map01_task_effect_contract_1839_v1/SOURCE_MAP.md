# Current-main schema map (intake `2ac5a00b`)

| Evidence plane | Existing source / observed fields | Boundary exposed |
|---|---|---|
| Physical actuation | `map01_v12_physical_occupancy_audit_v2/audit.py` and its README; Executor events `accepted`, `input_admission`, `keys_held`, `input_released`, plus nested physical-edge measurement | V12 admission/physical edges can be joined to accepted program lineage; ordinary key-up remains interval-censored in the v38/v39 posthoc record. |
| State feedback | `doom_typed_observation_v1.py`; event `typed_observation`, `sequence`, `capture_ns`, `signals.health/ammo`, binding and frame hash | Typed HUD state is observable state, not positive task effect or authority. |
| Independent scorer | `independent_progress_clock_v2.py`; `independent-progress-event-v2` carries sequence/time/kind/polarity/useful/controller_visible and before/after | Scorer is controller-invisible and monotonic within its own epoch, but the event schema itself does not carry plan/actuation IDs. |
| Old-evidence limit | `map01_first_useful_feedback_posthoc_v1/REPORT.md`; #503 result | v38/v39 can yield state feedback, but no retained plan-bound stronger effect timestamp; their run-level score is not a per-plan endpoint. |

Git blob identities at intake:

- scorer: `f95cd2b7b19c0d1ce699f840c2ae356c4b476601`
- physical audit: `8efa22d2bb60763a821c73b20b7ff016fd0e0fa7`
- effect receipt audit: `e60ea614fe4b9ef4b1d2d33900cfe9592b16c794`
- #503 report: `dddd317a58a880284a575b7aff89d926ef8a537c`

The synthetic contract therefore requires a separate immutable session/plan/
actuation binding to associate scorer output. The association is descriptive;
the scorer remains independent and controller-invisible. No claim is made that
the current live schemas already emit this complete joined receipt.
