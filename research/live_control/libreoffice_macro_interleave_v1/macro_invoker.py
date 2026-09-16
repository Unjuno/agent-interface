#!/usr/bin/env /usr/bin/python3
import json
import sys
import time
import uno


def fail(message):
    print(json.dumps({"ok": False, "error": message}, sort_keys=True))
    raise SystemExit(2)

if len(sys.argv) != 4:
    fail("usage: macro_invoker.py PORT BARRIER SLEEP_MS")
port = int(sys.argv[1])
barrier = sys.argv[2]
sleep_ms = int(sys.argv[3])
ctx = uno.getComponentContext()
resolver = ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", ctx)
try:
    remote = resolver.resolve(f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
except Exception as exc:
    fail(f"resolve:{type(exc).__name__}:{exc}")

desktop = remote.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", remote)
enum = desktop.getComponents().createEnumeration()
docs = []
while enum.hasMoreElements():
    component = enum.nextElement()
    if hasattr(component, "getDrawPages"):
        docs.append(component)
if len(docs) != 1:
    fail(f"draw_doc_count={len(docs)}")

doc = docs[0]
factory = remote.ServiceManager.createInstanceWithContext(
    "com.sun.star.script.provider.MasterScriptProviderFactory", remote
)
script = factory.createScriptProvider("").getScript(
    "vnd.sun.star.script:conditional_window_macro.py$apply_window?language=Python&location=user"
)
invoke_start_ns = time.monotonic_ns()
ret = script.invoke((doc, "A", 1000, 1200, barrier, sleep_ms), (), ())
invoke_end_ns = time.monotonic_ns()
print(json.dumps({
    "ok": True,
    "invoke_start_ns": invoke_start_ns,
    "invoke_end_ns": invoke_end_ns,
    "macro": json.loads(ret[0]),
}, sort_keys=True))
