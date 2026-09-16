# Inkscape AT-SPI selected-object identity across fresh sessions

Decision: **DEPENDENCY_UNAVAILABLE_ATSPI_SELECTION_SCOPED** for the queried public fields. This is a negative capability-boundary result, not a claim that Inkscape or AT-SPI never exposes selection by any route.

Task lineage: Issue #362. Allocation `INKSCAPE-ATSPI-SELECTION-IDENTITY-20260916-019` stopped for outer execution budget after three complete cases and three partial directories; those outcomes are retained separately and are not pooled. Successor `...-020` changed orchestration only and completed the frozen 12-case allocation. Publication BASE: `0a6012d189d2b4228d6f01462efc257e8d5e29dd`.

## Question

Prior #339 / PR #353 established that an unmodified Inkscape process can be read through a genuine explicit-address AT-SPI D-Bus connection and that ordinary public widgets expose working Selection data. The unresolved question was narrower: when the canvas independently shows none, object A, or object B selected, do the labelled document-object accessibility cells or their nearest public Selection ancestor expose which object is selected?

This experiment keeps the explicit-address transport fixed. It does **not** restore the missing standard registry/autolaunch service. It performs no AT-SPI writes, application edit/save/effect operation, model call, or game call.

## Construction and freeze

Fresh processes do not preserve AT-SPI object paths. An initial fixed-path construction was rejected. The harness was changed before measurement to rediscover `AI_Target_A` / `AI_Target_B` by public Accessible Name and to walk Parent links to the first Selection ancestor. A second construction problem was a harness performance bug: `dict.setdefault(..., Client(...))` constructed a new D-Bus client on every RPC even when the key already existed. It was fixed before measurement to reuse the existing connection.

Final construction none/A/B all passed: screenshot selection handles established the requested canvas state, the two fixture labels were dynamically found, an unrelated ordinary widget Selection object returned one named selected child, and the document cells plus object-tree Selection were readable.

Frozen hashes:

- `run_case.py`: `ec12975f12529e31e5df2c3b4d943ecc0e04f4d4be113e0d591657a675df0392`
- `native_dbus.py`: `3a6044c2f88d0828f50b5234f61390df46ee5876c1f2046fa802c481b6d3ea1e`
- `audit.py`: `67952bd1fb634f1488d9ceb522456ac7e626c68efa54956db6ed6f4098e8c0c1`
- original preregistration: `a156c9373160f1aa253228cdd9a4d5cc8f606a480d0742a82474c5f159c02146`
- successor orchestration preregistration: `b65b8116ee75206220cd00d55889b5763e3a082d43554167037f6d3f70b5454f`

Allocation 020 used the exact same randomized 12-case schedule as 019: four fresh processes for each of `none`, `A`, and `B`, shuffled once with `random.Random(35620260916)`. No threshold, queried field, setup rule, or decision criterion changed after first measurement.

## Result

All 12 fresh sessions completed and passed independent setup/control gates.

| Endpoint | Result |
|---|---:|
| Requested canvas selection independently established from handles | 12/12 |
| Fixture labels A and B dynamically rediscovered | 24/24 |
| Ordinary-widget public Selection positive control working | 12/12 |
| A cell public state vector | `[1463814400, 0]` in 12/12 |
| B cell public state vector | `[1463814400, 0]` in 12/12 |
| A or B cell reported AT-SPI SELECTED bit | 0/24 |
| Nearest object-tree Selection `NSelectedChildren` | 0 in 12/12 |
| SVG bytes unchanged | 12/12 |
| Empty key/button state at observation boundary | 12/12 |

The canvas setup distribution was exactly four none, four A, and four B. In every A case the screenshot handle check identified A only; in every B case B only; none cases showed neither. Despite those independently different canvas states, the declared target-cell state vectors were identical across all 36 target/state comparisons, and the nearest shared `tree table` Selection object always reported zero selected children.

The positive Selection control is important: in every session an ordinary public widget Selection object returned `NSelectedChildren=1` and a valid named selected child (`Dip pen`). Therefore the zero document-tree selected count is not explained by a decoder that always returns zero or an entirely broken Selection interface.

Fresh-process path identity was not assumed. In allocation 020 the dynamically discovered A/B paths happened to be `/org/a11y/atspi/accessible/3039` and `.../3037` in all 12 sessions; the nearest Selection ancestor happened to be `.../3004`. Those values are observations, not stable interface identifiers.

## Descriptive acquisition cost

Dynamic public-tree discovery elapsed median **5476.900 ms**, observed range **4820.813–10975.833 ms**, batch size one per fresh process. This is diagnostic whole-search time, not a qualified pre-input guard latency. It includes thousands of D-Bus reads and local recording work. No speed claim follows.

Executed environment: Inkscape 1.4 (`e7c3feb100`, 2024-10-09), CPython 3.13.5, Linux 6.18.44 x86-64, D-Bus 1.16.2, Intel Xeon Platinum 8573C shared host, process affinity CPUs 0–4, CPU operating frequency not pinned. Private Xvfb/Openbox and genuine private D-Bus daemons were used. The normal AT-SPI registry/autolaunch path remained outside this experiment.

## 019 infrastructure stop

The first frozen invocation, 019, hit the outer 60-second tool budget. Cases 00-none, 01-B and 02-A completed; cases 03-B/04-none/05-B had only partial directories and no result. 019 is `STOPPED_INFRASTRUCTURE`, not pooled with 020 and not resumed. Its complete and partial files are retained in the full conversation archive.

## ERROR CHECK

The independent auditor does not import the measurement runner. It verifies the frozen source hashes; exact 12-case schedule; successful setup/positive control; A/B labels; AT-SPI SELECTED bit; nearest Selection selected count; SVG preservation; and empty input state. Allocation 020 returns `PASS_ATSPI_SELECTION_UNAVAILABLE_AUDIT` with 12 rows and no errors.

Six post-measurement corruption controls are all rejected: forged target SELECTED bit, erased positive Selection count, hidden visual setup mismatch, forged SVG mutation, forged held key, and missing case. These controls add no live samples.

## H / T / D / C / U

**H:** the direct public AT-SPI route may expose the current selected document object through the labelled cell state or its nearest Selection ancestor.

**T:** 12 fresh unmodified Inkscape processes, four per none/A/B, with independent screenshot setup checks and same-session ordinary-widget Selection positive controls. Read-only accessibility queries only.

**D:** the hypothesis is not supported for the declared public fields. Retain `DEPENDENCY_UNAVAILABLE_ATSPI_SELECTION_SCOPED`. A universal controller must not infer A/B selection identity from these fields in this fixture.

**C:** another standard AT-SPI interface, event stream, properly registered desktop topology, or different Inkscape accessibility implementation may expose useful selection identity. The Objects panel may maintain a custom model not represented as AT-SPI Selection. These alternatives are unresolved.

**U:** explicit-address topology rather than standard registry/autolaunch, one Inkscape version/theme/backend, fixture-authored labels, limited queried fields, small finite sample and non-atomic multi-RPC discovery. This does not prove that all accessibility metadata is absent, nor that other applications lack semantic selection identity.

## Next single question

Do not tune another screenshot guard or repeat the same polling. The next information-bearing question is **event semantics**: while A/B selection changes, does the public AT-SPI route emit a standard state/selection/focus event that identifies the affected document object even though snapshot fields remain non-discriminative? If event subscription is unavailable in the explicit-address topology, retain that dependency gap rather than inventing a private application API.

## Retention

The full conversation archive is 10,780,376 bytes, SHA-256 `f85937813bcf3703b95a654f092bb77414022ffcbc2e6bb95f821ad994292961`, and includes bulk RPC/discovery logs, construction, stopped019 and completed020 evidence. GitHub retention uses a compact 189,976-byte archive, SHA-256 `6ca77754aeb5cb90e4db9444627ba602d107f13e54283c67aad559fe3bbd7f01`, containing exact sources/preregs/audits, every 020 `result.json`, setup images and input logs. Bulk traversal RPC/discovery logs remain conversation-retained; this boundary is explicit rather than being called fully GitHub-retained.
