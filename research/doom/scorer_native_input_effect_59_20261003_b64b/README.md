# #59 native POSIX input and scorer file-sink composition

Finite authored-cost Linux/arm64 experiment; no game/model/GUI/live allocation.
See [PROTOCOL.md](PROTOCOL.md), [SOURCE_MAP.json](SOURCE_MAP.json),
[construction/HISTORY.md](construction/HISTORY.md), and the eventual REPORT.md.

The original source and separately proposed #6913 engineering-v2 source are
copied unchanged. The candidate delegates instrumented clock/select/read calls
to real OS services, persists scorer rows through the exact ScorerFileSink,
and makes only a private disposable completion-file effect. All original
negative/diagnostic/partial outcomes remain. A finite sample-budget stop does
not establish infinite starvation; wall times are not general latency rates
or a measured speedup. Zero nonterminal ProgressSamples provide no real game
feedback or model benefit. No runtime/workflow source is patched.

Ordinary retained-mini regression: `python -B -m unittest -v construction_checks`
from this directory, also under `-O`. This only reads the preserved two-case
construction data; it invokes no candidate, container, native pipe or formal
auditor entry point. `construction_checks.py` is not a default test-discovery
filename. The formal candidate and auditor are separately allocated once;
do not invoke their launch commands as routine CI or overwrite their outputs.

Exact host receipts containing the private source path remain access-controlled
in the author's workspace. Public receipts explicitly substitute `{OWN_SOURCE}`
for that mount and bind the private original receipt hash. They are derivatives,
not verbatim original command bytes. RED diagnostic logs retain the same explicit
redaction mapping. Payload/trace/artifact bytes contain only authored fixture
data and native telemetry. Hashes identify retained records, not authenticity.
