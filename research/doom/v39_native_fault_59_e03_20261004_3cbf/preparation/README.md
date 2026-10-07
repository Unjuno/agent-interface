# Native-session preparation, not a formal E03 result

Issue #59; owner 3cbf. This directory preserves executed preparation for a
distinct native-session fault/recovery question. No formal protocol, allocation,
candidate adoption or research PASS is asserted yet.

Source: main `39551d89699910e054ad81bd1f94743f2d8cb6ed`. Git archive selected
1,915 top-level Python files in research/{doom,live_control,observation_gating,
observation_tiles,real_apps_v1}. Root package resolution was provided by
`PYTHONPATH=/source`; source bind mount was read-only. Exact staged source is
retained on the own VM at
`/home/taka/e03-session-preflight-3cbf-20261004/source/unjuno-e03-source.LyYTXP`.
These are preparation sources, not an attestation of every actually loaded module.

Own VM: research-6183-t0-20261003. No GPU/device/peer mounts or model calls.
Private image (after openpyxl installation):
`sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b`.
Actual ViZDoom 1.3.0 package-local freedoom2.wad SHA256:
`a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`,
matching the retained v2 fixture manifest. No saved fixture was loaded here.
Setup logs retain requested and transitive versions and apt output. This image
is not a reproducible published distribution or frozen final science image.

Both startup probes used network none, CPU1, memory1GiB/swap0, pids128,
read-only root/source, cap-drop ALL, no-new-privileges, UID501, tmpfs256MiB,
own writable output mount and outer `timeout 40s`. Configuration is recorded
in container receipts; live cgroup enforcement was not sampled in this step.
Input was exactly one JSON line: `{"op":"finish"}`. Command body:

```
python3 -B /source/research/doom/session_map01_v12.py \
  --out /out/preflight02 --seed 20261004 --timeout-seconds 20 --skill 1
```

## First outcome retained

Container e03-native-session-preflight-3cbf-20261004 used workdir `/source`
and relative script path. UTC 2026-10-03T20:41:18.492975867Z to
2026-10-03T20:41:19.072504971Z; exit139, OOMKilled=false. ViZDoom reported
`Failed to create ./_vizdoom/ directory: Read-only file system`.
`preflight01.*` and the first receipt preserve this failure. Not relabeled PASS.

## Distinct corrected-layout preparation

Container e03-native-session-preflight02-3cbf-20261004 changed workdir to the
own writable `/out`, script to its absolute read-only path, and output to a new
directory. UTC 2026-10-03T20:41:40.333106289Z to
2026-10-03T20:41:44.012225317Z; exit0, OOMKilled=false.

Actual X11/ViZDoom MAP01 window, ready, typed initial HUD health100/ammo50 and
matching later exact full observation were emitted. Clock advanced18 to89tic
during2.0364963000029093seconds with no advance calls during the wait.
One finish command reached post_control_score: alive, unfinished, no kills or
deaths. No submit/cancel/held-input or gameplay objective was tested.
Docker ps showed zero running containers after termination. No independent
process-level global input-neutrality or module-loading audit is claimed.

## Next research gate

Prepare and independently review a genuinely distinct frozen native fault
protocol before execution: can E02's typed receiver fault surface support a
bounded cancel/release response while an actual session action is in flight?
Transport fault injection must be labeled as controlled injection, not natural
game failure. Include a healthy control, source/module/image/runtime custody,
first failure retention, existing native release evidence, actual OS neutrality
checks and explicit stopping/cleanup. Do not take over 5ce3's selected-import
or per-key instrumentation work, 0820's cover-anchor candidate, or #6944/#7084
production adoption. E01/E02 consumed allocations remain immutable.

This preparation advances environment eligibility only. The research segment
remains incomplete until the distinct experiment, independent audit and
reviewed evidence delivery are done. No wrapper-only PR is warranted.
