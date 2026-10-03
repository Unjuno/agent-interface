# E04 preparation status

Formal native runs: **0**. Official saved-only auditor runs: **0**.
Frozen execution inputs at 96b72496f5e93937b52d1fd35513cc15f1da0426.
Independent Curie launch review READY, Critical0/Important0. Actual launch
still requires fresh ownership/path checks; no empirical PASS is implied.

Fresh construction verification: 24 unittest methods passed on host Python
in normal and -O mode, and 24 methods passed in own isolated CPU Docker
container e04-audit-construction-ci-3cbf-20261004. Container stdout/stderr and
terminal inspect are retained in methods/CONTAINER-CONSTRUCTION*.
This container executed tests only, no game or formal producer.

Retained E03 data are used read-only to test the NEW saved-audit entry; the
consumed E03 official auditor is not rerun. Initial missing-import handling
and invalid CLI JSON failures remain in methods/*RED*. The new audit returns
scientific_pass=false for that genuine partial startup STOP.

Independent integration review found four Important gaps: export equality,
imported-but-unexposed STOP wording, execution manifest closure, and undeclared
later-cell directories. All four are addressed in code; three new rejection
tests demonstrated RED then GREEN, with 27 methods passing normal and -O on
host. The disposition is conservatively exposure-unestablished for any failed
imported cell. Follow-up Curie review confirmed all four fixes and strict
integer timestamp guards; host normal/-O and own frozen-construction container
each passed28 methods. No component test count
substitutes for the native fault/cancel hypothesis.

E03 evidence delivery remains preserved on public branch
research/v39-native-fault-e03-3cbf-20261004 at
c612fd09e9be6ac98d3ed4cce1f08508d5cb9198; its PR creation was blocked by
GitHub secondary rate limiting. No alternate API write bypass is used.
