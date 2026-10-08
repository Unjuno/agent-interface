# First primary stdio terminal attempt: retained limitations

Source c999e2d6c (full revision/archive identity in manifest.json), before the
terminal-output guard. One actual Windows PTY -> WSL -> packaged primary CLI ->
Python relay -> nonpersistent public MCP connection. No application/display,
native input or screenshot was launched. Existing prior studies were not rerun.

Clock returned; invalid static program returned its original MCP error and
latched primary STOP; ordinary observe was blocked locally without a fourth
public request. Explicit interface_close was sent but refused with Unknown tool:
interface_close because this nonpersistent server configuration exposes no such
tool. Preserve this failed public-close outcome; transport EOF/exit 0 is not a
successful public close. Exact public requests were clock/validate/close (3).
Local command IDs 1..4 include the stopped observe, which consumed a local ID
without an extra MCP call. No native backend or input was invoked.

The Windows terminal rendered long JSON with ANSI cursor control, visual wraps
and duplicated display characters in the returned tool transcript. It cannot be
treated as a byte-exact JSON-lines channel. Original exchange/host records remain
valid; the exact original own tool/usage rows, including that rendered output,
are retained in actual-source-records.jsonl. No reasoning or other chats included.
No provider token/cost result or GUI/model efficiency benefit is inferred.

After this owner was terminal, candidate code was changed to refuse TTY stdout
before starting a host; use a managed pipe/file for machine JSON. It also retains
an original output exception through cleanup instead of attempting another write
to that broken output in finally. Nine focused tests pass, including pre-start
TTY refusal and one-relay cleanup/one-write original-error preservation.
Earlier 178-node/9-distribution results apply to the pre-guard source; corrected
source validation is separate and will be retained with its own source pin.
No in-place code/reply/image changes or replacement of this first attempt occurred.

The default MCP example for real guarded GUI use needs guarded-x11 and an owned
display/window. This nonpersistent clock/refusal probe does not validate that
GUI configuration, public close, image delivery, human tempo or token compression.
