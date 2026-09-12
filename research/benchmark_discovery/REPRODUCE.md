# Reproduce the discovery evidence

This is a Linux/X11 feasibility harness, not a benchmark runner or an autonomous
agent. It launches private Xvfb/Openbox instances and issues no game input.
Use a new output path on every run; existing outputs are rejected.

## Assets and environment

Ubuntu 24.04 x86_64, Python 3.12, Xvfb, Openbox, wmctrl, Mesa software GL,
Python Pillow/Xlib/NumPy/openpyxl are required. The harness imports the existing
`research/observation_gating/gui_suite.py` and its real-app session wrapper.
See `environment.json` and per-run manifests for measured environment details.
No system package installation was performed in this study.

`assets.json` lists 38 actual downloaded archives, totaling 165,858,524 bytes.
This includes the abandoned old Minetest proxy and dependencies shared by
multiple candidates. It is not a per-candidate minimum or installed size.
Ubuntu archive hashes were checked against the available apt package metadata;
the Luanti package hash was checked against the PPA package index reached from
the official downloads page. Release/archive availability can change; any
replacement version requires a new study ID and manifest, never a silent update.

From the repository root, in Linux:

```sh
python3 research/benchmark_discovery/prepare.py \
  --root /home/taka/agent-interface-bench-feasibility --download --extract
```

Without flags the command only verifies existing asset bytes. Extraction goes
to private `root/` and `luanti-root/` prefixes. Missing system libraries must be
resolved explicitly, not by mixing unrecorded alternate binaries. The extracted
Java package retains absolute configuration references: the study logged HTTPS
initialization errors in ancillary startup checks. This reproduction preserves
that limitation; repair/pin an isolated Java configuration before formal use.
The download helper was verified against existing assets; a new complete fetch
with this helper was not timed or used as the installation measurement.

## Final discovery cohorts

These commands reproduce the respective final smoke conditions. Use an absolute
repository path when invoking from another directory. The working examples use
the same asset root as above; `--root` can point elsewhere.

```sh
python3 research/benchmark_discovery/smoke_v7.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/feasibility-rerun/openttd --app openttd
python3 research/benchmark_discovery/smoke_v5.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/feasibility-rerun/mindustry --app mindustry
python3 research/benchmark_discovery/smoke_v4.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/feasibility-rerun/luanti --app luanti
```

Run games sequentially. Take resource comparisons only under controlled host
load, with matching declared workloads. Window appearance is logged but is not
a semantic readiness time. Screenshots follow a fixed warmup/sample interval;
inspect source PNGs at original resolution and confirm engine/scenario state.
The known image-presentation issue means a seemingly blank tool image must be
checked against saved source bytes before blaming the engine.

Fresh game configuration lives under a private temporary HOME/XDG and X server.
OpenTTD data directories are linked into that private profile. Mindustry uses
`MINDUSTRY_DATA_DIR` and a setup-only mod. Luanti uses its authored game and a
native Linux temporary world, copied to output after shutdown. Its local server
binds loopback. SIGTERM is attempted, followed by bounded SIGKILL when needed;
all owned processes are reaped. This is process reset, not proof of reliable
save/load or crash recovery. No persistent shared-runtime semantics are changed.

## Historical cohorts retained

| Cohort | Harness | Content / interpretation |
|---|---|---|
| 01 | `smoke.py` | OpenTTD language-data failure, Minetest 5.6.1 font crash; two attempts each |
| 02 | `smoke_v2.py` | OpenTTD data links repaired; Mindustry menu; two attempts each |
| 03 | `smoke_v3.py` + `luanti_game` | current Luanti, world on `/mnt/c`, original camera/physics; two attempts |
| 04 | `smoke_v4.py` | `luanti_game_v2` pad/native-world smoke; original Mindustry mod failed on JS Double setting; two each |
| 05 | `smoke_v5.py` + `mindustry_mod_v2` | Java Integer setting fixed; Fork loaded and tile/core oracle recorded; two attempts |
| 06 | `smoke_v6.py` + `openttd_script` | GameScript name parsing failed; live GUI did not imply oracle success; two attempts |
| 07 | `smoke_v7.py` + `openttd_script_v2` | unspaced GameScript name; read-only initial rows and target count; two attempts |

Harness versions preserve failed experimental source bytes. Plan amendments are
separate files. Game/mod fixtures were not included in the initial harness-only
source manifest; the post-study `provenance.json` freezes their present bytes
and the imported session dependencies. This is a stated provenance limitation,
not a claim that every input was preregistered before every exploratory run.

Run `python research/benchmark_discovery/audit.py` from the repository to verify
the archived cohort hashes/metrics and partial-state comparisons. It audits the
committed cohort paths, not arbitrary rerun directories, and it does not launch
games. `audit-summary.json` is derived data. The observed Mindustry initial-state
discrepancy is an expected discovery finding, not a reason to reject the audit.
Read-only positive/negative/near-miss scoring controls and task-level shared
interface input remain prerequisites for promotion beyond feasibility.
