# #5260 A03 construction report

One invocation, eight fresh app processes, no input and no retries:
2026-10-03 13:30:18.234878–13:30:31.766234 UTC, exit0, 13.5302 host seconds.
The observed wall time is not a performance comparison.

| Mode | Fresh apps | Schedule / focus / finalization | First-observed / final epoch | Input events |
| --- | ---: | --- | --- | ---: |
| LEGACY | 4 | 2 / 2 / 2 in all4 | 1 / 2 in all4 | 0 |
| FIXED | 4 | 1 / 1 / 1 in all4 | 1 / 1 in all4 | 0 |

Each replicate contains both modes, with alternating order. The matched
private apps use the same geometry and container; the corrected mode
claims before `update_idletasks()` and before finalization. Legacy uses
the inherited claim-after-update pattern. No XTest import or key/click
injection exists in these probe sources; both fields remain empty.

H: Map/Configure callback reentry before the old ready-written flag can
schedule more than one finalizer and decoy-focus callback.
T: seven callback adversaries, then the prospectively identified no-input
private-Xvfb construction. Independently reconstruct sources, schedule,
PIDs, clocks/events, all app/ready/stream bindings and host receipt hashes.
D: corrected rows have one finalization and unchanged first/final ready
identity; construction failures would be retained without automatic retry.
C: pinned same WSLc image, owned private display :97, fresh apps, alternating
mode order, identical size/layout; no user desktop/network/GPU/model/input.
U: one disposable Tk construction; no inference about real client typing,
useful feedback or throughput, population error rates or Docker parity.

The observations support callback reentrancy as a mechanism of readiness
overwrite in this derived construction. They do not establish that it
caused A02's31 nonexact saves, or that eliminating it recovers typing.
The A02 raw and original/stronger audit outcomes remain unchanged.

Independent post-outcome auditor: `PASS_CONSTRUCTION_CUSTODY`, errors[].
All8 app PIDs/exit0; Xvfb/Openbox exit0; ready geometry/clocks mapped and
positive; candidate host stdout summary8/0 agrees with the row records.
First captured audit 13:36:09.540337–13:36:09.657864 UTC, exit0.
Earlier uncaptured local read-only reconstruction passes occurred during
auditor development; these did not start another app or container.

Runtime: Debian `/usr/bin/python3`3.13.5/Tk8.6/linux-amd64, image ID
`sha256:217851fe68e7340cd6301e6d1a1bd79d2c7b6cb4d13eb444a06fabaf0fde3417`.
CPU0.5/512M are requested, not independently proven effective. The original
WSL swap-limit warning, X11 non-root socket warning, Openbox home/cache/menu
warnings and all8 Fontconfig warnings are retained. No shared service,
runtime configuration, reservation or other agent's process was changed.

Raw SHA256 `322f096e20d22627baeb54aecf9bb4bab3e32ce539bbd0decae5cbdbb916f657`;
construction freeze `c81d45f9f58a217a162a72800d4e5090a9db14c15442d698d4abebf260a23123`.
GitHub prospective #5260 comment5969638139; resource allocation #5085
comment5969638282; resource completion/release5969651383; result5969722659.

Next: independently integrate this helper; then use a fresh input protocol
that gates immutable readiness identity, not the consumed A02 allocation.
Keep #5260/#5296 open. The repository's broader roadmap is not complete.
