# Native observation artifacts used by the primary assistant

2026-09-19. This successor uses the opt-in `capture_directory` path in the
public golden/native dispatch API. The assistant viewed `before.png`, an exact
copy of the initial native observation's PNG, chose `[130,55]` and
`artifact991079`, then viewed the native action observation `native-after.png`.
The existing fixture independently saved exactly `artifact991079`.

Two PNG files were encoded from the same GetImage replies whose raw hashes are
in the returned native observations. Both image-file hashes and source raw-hash
links were checked during retention. The test suite also verifies pixel colors
for both byte orders, a single GetImage call, and retention of raw evidence on
artifact-write failure. It has 26 passing tests across encoder, native boundary,
public API and result mapping.

The action's native PNG still shows the **unsaved** state. The later independent
scorer confirms the save, and the separately captured `after.png` shows it. The
native PNG was not replaced with that later image. This demonstrates why capture
identity and application-effect completion must remain separate. A subsequent
native-observation continuation is still needed for late rendering; this run
does not implement that continuation or visual target revalidation.

The stale-source control returned STALE_OBSERVATION with zero input emissions.
Initial observation and accepted input both verified empty release. The fixture
and private Xvfb were reaped; `cleanup.json` records their return codes.

Local timings: dispatch 136.767879 ms; call start through independent scored
effect 196.913505 ms; entire harness including primary-assistant wait
32555.786395 ms. Artifact encoding/persistence is included in dispatch. These
are sequential single-run observations, not matched speed comparisons. No
helper model was called. Primary-model tokens/cost are unavailable.

Reproduce using the dependencies and local package setup documented in
`../native-result-self-use-01/README.md`, then run:

```sh
XAUTHORITY= python3 -m runtime.native_result_self_use --native-artifacts --out NEW_DIRECTORY
```

View the new `before.png` and supply that run's `request.json`. Initial and action
programs/results are preserved. Historical artifact paths in those results refer
to the original results-local directory; archived copies are in `native-images/`
with the same basenames and content hashes. `SHA256.json` covers evidence and
source snapshots, excluding this README. The prior unsuccessful task and setup
attempts remain in the predecessor archive without edits.
