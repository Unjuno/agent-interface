# Issue #7825 A01 — finite historical receipt-authenticity method test

Status at source freeze: formal candidate 0, independent auditor 0. See `FREEZE.json` for pinned source/input hashes, runtime image, exact invocation gates and no-retry rule. Construction records are separated under `construction/`.

The fixture compares independently registered period/slot keys, a finite Merkle/Lamport key-evolution frontier, and the latter with an independent checkpoint witness. Its current-period compromise seeds are intentionally public synthetic attack inputs. They are not production secrets. The fixture uses one-time leaves; every attack case is a separate fork of the same pre-compromise snapshot.

The intended conclusion is narrow: on this finite fixture, historical-forgery rejection is the same for simple rotating keys and the evolving tree. The evolving tree has no distinct historical-forgery advantage in this test. External checkpoints add detection of tested latest-head rollback/fork/suffix changes; an authentic signature or checkpoint does not prove a claim is true.

No real secure erasure, production FSS security, trusted time, honest witness publication, runtime integration, GUI, model, user input, external effect, safety, or resource-enforcement claim is made. WSLc accepted `--memory 512M`, but its kernel reported that swap limits/cgroup enforcement were unavailable; the setting is not treated as a proven hard cap.
