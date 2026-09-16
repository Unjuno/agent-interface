# Inkscape direct public AT-SPI reads: scoped prerequisite result

**PASS_DIRECT_WIDGET_READ_ONLY. Standard registry/autolaunch remains unavailable. Document-selection identity remains UNTESTED.**

Issue #339; task `INKSCAPE-ATSPI-DIRECT-READ-20260916-018`; immutable publication BASE `0dd239b7db10831a4e8ac078d3a32d4be6370e3d`. Additive research only; no shared runtime, historical allocation, scorer or workflow change.

## Intervention and limits

The previous 016 preflight found that installed libatspi/ATK libraries did not imply a usable standard accessibility service. The earlier audit was reproduced offline without rerunning that live allocation. Package acquisition again failed to deliver bytes; no package was installed.

Instead of fabricating a registry, the new diagnostic configured the existing upstream-supported `AT_SPI_BUS_ADDRESS` to a separate genuine private `dbus-daemon`. Unmodified Inkscape's installed ATK bridge exported standard public Accessible objects on that transport. This is an explicit topology change, not a claim that normal AT-SPI discovery, registry, event subscription, or native-client completeness has been repaired. Upstream source reference: GNOME/at-spi2-core `atspi/atspi-misc.c`, blob `f3124965f07ddf2db5f67bacffbc228cb977eeb1`.

## Frozen experiment

Issue #339 comment 5696178084 froze the source and exactly three first fresh sessions before execution. Prereg SHA-256 `d5ff93795a2ff08bd589cd4c3250cbbc4e396ba77a96caf49dc95bace4bbd863`; runner SHA-256 `7e8e50e1b9f6ea3d192cf7af4b5c1670a6e59ac8fcb86a36d56fe88d8d987961`.

Each new private session launched Xvfb/Openbox/Inkscape with a disposable two-rectangle SVG. The destination was bound to the spawned Inkscape PID using `GetConnectionUnixProcessID`, not assumed from a bus name. After a five-second startup allowance, reads were bounded to 256 nodes/depth30/26 seconds, with 1500 ms RPC reply timeouts. Only properties, roles, children, interfaces and bus metadata were read. No Action method, selection-write method, XTEST, model or game call was made.

| Endpoint | Session 1 | Session 2 | Session 3 |
|---|---:|---:|---:|
| PID-bound public widget read | PASS | PASS | PASS |
| Named button positive controls | 3 | 3 | 3 |
| Structured Accessible nodes read | 256 | 256 | 256 |
| Logged RPCs including discovery controls | 1027 | 1027 | 1027 |
| Unvisited queued nodes at the cap | 302 | 302 | 302 |
| Normal org.a11y.Bus autolaunch | FAIL | FAIL | FAIL |
| Registry present | No | No | No |
| Unchanged SVG / empty keymap | PASS | PASS | PASS |

The named controls were `Reset to simple snapping mode`, `Advanced mode`, and `Open Collections Editor`. Each has a nonempty name, button role and advertised `org.a11y.atspi.Action` interface. Raw identity/discovery/widget replies are GitHub-retained witnesses. Advertising Action is not invoking it.

The tree is bounded and incomplete; no document-selection transition was tested. Missing objects must not be labelled absent. All three records keep document-selection identity UNTESTED. This result removes a blocker for direct read-only investigation, not for ordinary registry-dependent clients or atomic action admission.

## Failures and audit

Construction retained an old role-name assumption (`push button` versus the installed runtime's `button`) and an XAUTHORITY/error-path harness defect. These were corrected before source freeze. No measured session was replaced, extended, or retried.

The frozen auditor initially failed because its `measured-*` glob included log files as well as directories. It remains unchanged. A separately retained `audit_v2.py` changes only the directory filter; no live run or raw result was changed. The corrected independent checker passes the three full traces. Eight post-measurement corruption controls are rejected, including wrong PID, fabricated registry repair/selection absence, input injection, changed SVG and invented tree completeness. This is same-session independent checking code, not independent-agent review.

All owned children were reaped. Inkscape was deliberately terminated by SIGTERM (-15); Openbox, direct bus and Xvfb exited. No held-input crash/release claim is made.

## Environment

Intel Xeon Platinum 8370C shared host, CPUs0..4, clock unpinned; CPython3.13.5; Linux6.18.44; Inkscape1.4; libatspi/ATK bridge2.56.2-1+deb13u1; dbus-daemon1.16.2-2; Xvfb1024x768x24; actual Python-Xlib `(0,15)`. No 0.33 execution claim. Exact inventory/binary hashes are retained. No latency benchmark, speedup, combined timing uncertainty or hardware real-time guarantee is claimed.

## Reconstruction and honest evidence boundary

The four parts form one 19,176-byte lossless compact archive with exact executable sources, both auditors, preregistration, all structured case results, raw positive-control/PID/discovery witnesses, validation receipts and a longer report. Part byte counts/SHA-256/Git blob identities are in `manifest.json` and were matched to MCP upload returns.

Run `python reconstruct.py /tmp/atspi-direct-evidence`, then `python /tmp/atspi-direct-evidence/study/verify_witness.py /tmp/atspi-direct-evidence/witness-01.json` (repeat for 02 and 03). These commands issue no GUI/input calls. The complete conversation archive additionally contains bulk raw traversal, construction traces and screenshots: 191,004 bytes, SHA-256 `f23a0da76ad7466912375b24c245104fd4ea19757ba37de1b5b1ab2a027e0576`. Those bulk payloads are NOT claimed retained on GitHub. Its 66 manifest entries and full audit were reproduced after fresh extraction.

## H / T / D / C / U

H: direct standard AT-SPI widget reads can work through an explicitly configured private bus even when standard launcher/registry discovery is missing.
T: three frozen fresh sessions; no task input; separate offline corruption checks.
D: retain direct read-only diagnostic capability. No production or selection-guard promotion.
C: manual topology and absent registry/event services may limit other clients and later operations.
U: one app/build/host, bounded tree, no selection transitions, effect verification or atomic semantic guarantee.

Next single question: with this transport fixed, does an A-selected/B-selected/unselected sequence expose a public document-object identity, not merely toolbar state? Freeze the identity criterion and preserve a known-widget positive control before interpreting a negative result. Do not change guards, polling or the application at the same time.
