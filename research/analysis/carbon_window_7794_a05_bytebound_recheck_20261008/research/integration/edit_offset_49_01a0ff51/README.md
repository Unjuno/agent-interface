# Native edit-offset boundary — Issue49

The unchanged Agent Interface X11Backend replaced text through real XTEST input
in32 fresh Qt5/X11 cells. Untyped numeric offsets produced8 wrong saved effects
out of16 constructed edits. Explicit scalar/UTF16 lowering plus SHA256 source
binding produced12 exact edits and4 zero-input refusals. The same independent
saved-UTF8 oracle detects baseline errors after they occur. This is a narrow
research adapter result, not an existing production defect or complete EditContext.

| Case, both widget types | Untyped saved result | Typed saved result |
|---|---|---|
| S01 ASCII `PABCDZ` | `PABXZ` | `PABXZ` |
| S02 `😀ABCDZ`, backward scalar5→3 | `😀AXDZ` | `😀ABXZ` |
| S03 `👩‍💻ABCDZ` | `👩‍💻XCDZ` | `👩‍💻ABXZ` |
| S04 `🇯🇵ABCDZ` | `🇯🇵XCDZ` | `🇯🇵ABXZ` |
| S05 decomposed `éABCDZ` | `éABXZ` | `éABXZ` |
| S06 context `PABCDZ`, current `QPABCDZ` | `QPAXDZ` | unchanged `QPABCDZ`, STALE_SOURCE |
| S07 unknown unit, `PABCDZ` | `PABXZ` coincidentally | unchanged, UNKNOWN_UNIT |
| S08 already-native UTF16, `😀ABCDZ` | `😀ABXZ` | `😀ABXZ` |

Each accepted program uses main core admission, focus/text X/release_all;4
physical emissions, one observed text change, no replay. All32 app/Xvfb exits
are0, endpoint server keymaps are empty, and release readbacks are verified.
The full raw stream SHA256 is
`1e6eb71c9b82941af761f677d7fca9a34458fa9cfb1cfef503aeec39cd858c49`.
The frozen raw-only auditor rejected all13 semantic corruptions, including
rejoined state/journal/saved-text substitutions. Image dimensions/hashes are
checked; saved text is the effect oracle. PNG glyph/font appearance is not OCR
or evidence for Unicode semantics. Root inspected the S02 plain PNG pair.

The source was fixed at `af6dd720cb5a38b0b4c8d18fe5907e4b65d2aa24` and publicly
read back from freeze commit `531b6433b1` before either formal invocation. Freeze
SHA256 `0034781948ee8f216054f419e0e38bb297aad6b678ef267340faab53ffe5a0b8`
pins21 files and new study `EDIT-49-X11-OFFSET-20261003-01`.
One candidate/one auditor/zero retries. Candidate output330169 bytes under the
2MiB cap. Separate auditor output7552 bytes. Candidate/auditor receipts both
record EXIT_ZERO_SOURCE_EQUAL. Actual timestamps, full argv, image/host resource
configuration, container identities/status, remote source hashes before/after
and output bytes are retained in [formal/01](formal/01/).

Installed environment: Ubuntu arm64, Python3.12.3, Qt5.15.13/PyQt5.15.10,
Linux7.0.5 OrbStack, child image
`sha256:65ae56ebdddc2742bc1441ee9eca0fcca7e232cb611a09ea8b177b36fc23c291`.
Physical Mac64GiB/10logical CPU with other running guests; no exclusive host
performance claim. Each run requests0.5CPU/512MiB/128pids, networknone,
read-only root/source, private64MiB tmpfs and dedicated output. Docker inspect
configuration is not empirical resource-enforcement evidence. No model/GPU,
host GUI/user clipboard, shared daemon or another worker's display is used.
The own VM is stopped at closeout; containers/image/evidence remain retained.

Eight focused policy/oracle tests passed in the same pinned Linux image, as
recorded in `construction/tests01.receipt.json`. Later runner cleanup changes do
not affect those exact test definitions/dependencies; construction03 exercises
the finalized runner's conversion/refusal paths. Construction01 has4 successful
native cells. Construction02 STOPPED in its first untyped P02 range inside a
surrogate pair: the app selection reply raised UnicodeEncodeError/EOF, before
the replacement program. Its original3 artifacts/source/container exit1 and
missing native app exit are retained. Construction03 has12 successful different
repair/control cells. These17 attempted construction cells are never pooled with
formal32. The missing-Xlib dependency container, policy import-red, original
raw auditor KeyError and subsequent raw-only correction are also preserved.

Read-only reanalysis, with a fresh output filename, from this package:

```bash
python3 -B audit.py --cases cases.json \
  --evidence formal/01/formal01/collected/formal01 \
  --output /path/to/fresh/audit.json
```

Do not replay consumed `formal01` or silently overwrite receipts. Future native
work needs a genuinely different question/input/authority and prospective freeze.
No production default, CLI/MCP schema, workflow, shared implementation, test
discovery or common index changes. The vendor's three implementation files are
exact Git bytes from `fb556b3d8bf5bae54a1f23b89fe2c2b5a2685df7`; four empty
research namespace initializers avoid importing unrelated runtime sessions.
This tests that backend/core boundary, not the public host/MCP/session route.

Adopt the conventional unit conversion for this constructed adapter question;
do not invent a learned range resolver. Retain post-effect verification.
Runtime adoption remains HOLD pending a real semantic-state source, scoped target
identity, composition/edit-operation semantics and current-state invalidation
at actual native admission. Two widgets share one Qt engine and are not two
independent applications. S06 is staged stale content, not a concurrent change
after admission. SHA256 equality is not adversarial collision resistance proof
or an atomic compare-and-edit API. The fixture exposes synthetic current text
to the controller; no claim about privacy-redacted accessibility is made.

No grapheme segmentation/atomic deletion, partial-cluster method PASS, IME,
normalization equivalence, Calc/XTerm acceptance, durable fsync, model/human
benefit, latency/tokens, global release/watchdog guarantee, or #49/#57/#59
completion. The larger Issue49 Unicode refinement also requires precomposed,
partial-cluster, no-edit, visual baseline and application comparisons; this
unit does not close that full gate. Qt6's current [QTextCursor specification](https://doc.qt.io/qt-6/qtextcursor.html)
motivates the unit distinction; observed Qt5 document counts/ranges here provide
the installed-backend evidence. See [prospective H/T/D/C/U](PREREGISTRATION.md).
