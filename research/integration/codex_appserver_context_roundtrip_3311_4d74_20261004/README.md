# Local app-server tool-result context round trip

This experiment checks one endpoint boundary after G16: when a client answers a
registered dynamic tool call with typed partial-state text and an image, does the
ChatGPT.app-bundled Codex app-server place those items in the next Responses
request? A local mock Responses endpoint captures that request and returns a
fixed response. No external model/provider, GUI, native input, or new task
effect is involved.

## H / T / D / C / U

- **H:** the app-server normalizes `contentItems` from a successful dynamic-tool
  result into the next model request, retaining both its typed text and image.
- **T:** launch the installed app-server binary once, start one ephemeral
  read-only thread, return one predetermined function call, answer it with the
  G18 final PNG plus a frozen partial-state marker, and inspect the second
  request received by a loopback-only mock endpoint.
- **D:** confirm exactly one tool call and two mock Responses requests; the
  second request contains the exact marker and the source PNG's SHA256.
- **C:** this establishes local app-server request serialization only. The mock
  does not establish that an actual provider ingests, attends to, or understands
  the serialized content. It does not test G18 accuracy, task completion,
  efficiency, or the WSLc app-server build used for G18.
- **U:** one round trip on the ChatGPT.app-bundled `codex-cli 0.159.0-alpha.12.1`
  build, one image, and one typed partial result.

The input PNG is the exact public G18 final capture retained in PR #7221, copied
byte-for-byte (SHA256 `6331fd4bb0f62dbb6d8492e0c71a4ad6bf1b98091f39b452e2279e7cfd3e6bcf`).
The mock's fixed final message is a protocol control, not a model judgment.

## Reproduction

`FREEZE.md` records the binary and source identities, frozen payload, and exact
command. The one-shot runner refuses to replace `RAW.json`:

Run the following in a fresh scratch copy when reproducing; both programs refuse
to overwrite existing outputs:

```sh
scratch="$(mktemp -d)"
cp research/integration/codex_appserver_context_roundtrip_3311_4d74_20261004/{run_roundtrip.py,audit_roundtrip.py,input-g18-final.png} "$scratch/"
python3 "$scratch/run_roundtrip.py"
python3 "$scratch/audit_roundtrip.py"
```

The mock binds only to `127.0.0.1`, uses a non-secret test bearer value, and
captures request summaries without authorization headers or full image data.
The first private capture also included the local app-server's ambient Codex
instructions and memory in the provider request, as expected for a model
context. Those bytes were sent only to the loopback mock and are retained only
in ignored `RAW.private.json`; `REDACTION_PROVENANCE.json` links its hash to the
public derivative. `RAW.json` keeps the exact test marker and image hash while
replacing other text with byte counts and SHA256 values. The public reproduction
runner applies this redaction while collecting requests. `AUDIT.json` records
the initial raw-only audit before redaction; `PUBLICATION_AUDIT.json` checks the
public derivative and its allowlist. No external inference request was
configured; OS-level egress was not packet-audited.

## Interpretation

If the raw audit passes, the exact content was serialized into the second
request sent by this local app-server process. It remains unknown whether a real
provider receives or attends to that content. The result does not replace the
G17/G18 model observations and is not an integrated reporting repair. Any
whole-path current/compiled comparison still needs a prospective matched task
and must count the extra turns, costs, abstentions, and independent effect
evidence.
