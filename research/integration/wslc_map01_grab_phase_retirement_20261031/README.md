# Deadline retirement inside versus after an X11 server grab

This isolated WSLc test extends #9903. A prestarted owner records X11 input custody, grabs the private Xvfb server, checks a HUD crop on the same connection, and sends `f` down. In `inside` mode it holds the server grab and stalls; in `crash` mode it ungrabs first and then stalls with the key still down. An 800 ms owner deadline causes worker retirement in both modes. A separate X11 probe, connected before the owner starts, issues a synchronous focus query after the down receipt appears. A separately prestarted cleanup worker then checks the retired owner and requests release of the recorded key.

| Run | Owner stalls | Probe response time | Key after owner → after cleanup | Ammo: before → after cleanup → later |
| --- | --- | ---: | --- | --- |
| ad01 | after ungrab | 0.80 ms | down → up | 50 → 48 → 47 |
| ad02 | while grabbed | 788.07 ms | down → up | 50 → 48 → 48 |
| ad03 | while grabbed | 788.71 ms | down → up | 50 → 48 → 48 |
| ad04 | after ungrab | 1.01 ms | down → up | 50 → 48 → 47 |

In both inside-grab cases the probe started before the owner deadline and completed after it, consistent with the server grab blocking its synchronous request until owner retirement. In all four, the parent saw the key down after owner retirement and up after cleanup; the cleanup worker also recorded empty tracked-key readback. Its receipt retains `cleanup_status: UNKNOWN`, `release_confirmed: false`, `task_success: null`, and `replay_allowed: false`: readback is not proof of complete queue drainage or exclusive input state. The scripted late artifact was absent after its scheduled time, but that is not a universal no-late-input guarantee. Game ammo differs between conditions; these non-atomic samples do not establish exactly when shots occurred or what a killed worker would have done under other scheduling.

Four fresh private Xvfb WSLc containers used Freedoom2 MAP01 ASYNC_SPECTATOR 35 tics/s, skill 1, seed 991031, one CPU, 1 GiB, no network, image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25, and a 20-second external timeout. Order was after-ungrab/inside/inside/after-ungrab; main was 0161689d6d4e899e89f627901a708246c94ee914. Mounted Python runtime matches 6a9c787d2caf9740612de65bd2539846dd87cad4 as recorded in #9891; intervening main commits add research only. ZIPs retain source, probe and custody records, receipts, samples, conditions and exit codes. `python audit.py` checks identity, probe/deadline ordering, worker retirement and cleanup. This is deadline-driven worker termination, not a host crash, robust product recovery, MAP01 completion, or a general latency bound.
