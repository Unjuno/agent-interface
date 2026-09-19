# Primary use with direct MCP image forwarding

The SDK driver returned each complete CallToolResult as one JSON line. The
orchestration forwarded text blocks with text(block.text) and image blocks with
image(block), without decoding a presentation PNG or calling view_image.
The primary assistant saw the initial image and public goal, authored the same
18-chord move/save recipe, then saw the final image through this path. Raw MCP
responses and original harness image artifacts remain retained for audit.

This removes two explicit image-view tool calls from this trial, compared with
native-mcp-timed-01. It remains a shell/SDK composition, not registered host
tools. Input decisions still use the explicit decision file. No image resizing,
receipt filtering, sensor work or runtime behavior changes were introduced.

Inkscape seed 991119 saved x=86, y=50, width=40, height=30 without transform.
One program emitted 43 operations; release was verified empty, feedback matched
and cleanup reported completed. The first status call returned needs_review
because owner inspection saw a terminal process before Popen.poll supplied the
exit code. The second read of the same allocation returned terminal/code 0;
there was no restart. Both status responses are retained. Exec 86020 exited 0.

SDK submission took 1022.469 ms, with 1003.359 ms inside the exchange and
19.110 ms combined outside it. This does not establish a speedup over the prior
984.206 ms SDK trial. Host image presentation and model interpretation remain
unmeasured, and removing two tool calls does not measure actual token savings.
This is one ordered successor, with a different seed and uncontrolled load.

Run `python3 runtime/results/native-mcp-direct-image-01/audit.py` to verify 50
manifest files, exact MCP image bytes against original harness artifacts,
request identity, independent SVG geometry, release, final owner status and
nested SDK/exchange times. Unlike the previous archive, this manifest includes
audit.py; this README was added afterward. PLAN.md precedes allocation and
client.py is the exact driver. Production runtime source was unchanged.

The forwarding snippet below describes the successful boundary. It requires a
complete, untruncated JSON result; incomplete output must be reconciled on the
same process, never treated as permission to repeat the GUI action. Chunk
assembly and output-size handling are still host responsibilities.

```js
const envelope = JSON.parse(completeLine);
for (const block of envelope.mcp_result.content) {
  if (block.type === 'image') image(block);
  else if (block.type === 'text') text(block.text);
}
```
