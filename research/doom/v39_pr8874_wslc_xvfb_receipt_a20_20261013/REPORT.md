# Recovered-source V4/V12 explicit-up A20

One WSLc Xvfb run through the PR #8874 `actual_source_recovery` owner snapshots observed a matched KeyPress/KeyRelease and independent keymap down/up. The wrapper produced `owner_thread_keyup_verified=true`, one identity-bound owner receipt and a verified empty close; the thread stopped and Xvfb exited 0. The A18 analyzer rejected the unchanged stream (`measurement_ready=false`, malformed admission 1, invalid release 1): admission omitted top-level `owner_id`; this snapshot's single-up result left `owner_transition_verified=null`. Raw SHA-256: `f9e270ac3db13b574ba886a8bacf865421a892d85659ca793a5c7598805970a7`. Independent recomputation is saved in `results/a20-01/audit.json`.

A20's V4 is an older recovery snapshot, not the A09 current-main V4; see A21 for the exact current-main freeze. Synthetic Xvfb only, no application/game effect or live allocation.
