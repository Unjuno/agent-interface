"""No-input X RECORD payload construction probe; never dispatches XTest input."""
import json
import threading
import time
from Xlib import X, display
from Xlib.ext import record
from Xlib.protocol import rq

owner = display.Display()
control = display.Display()
events = []
ctx = owner.record_create_context(0, [record.AllClients], [dict(
    core_requests=(0, 0), core_replies=(0, 0), ext_requests=(0, 0, 0, 0),
    ext_replies=(0, 0, 0, 0), delivered_events=(X.KeyPress, X.KeyRelease),
    device_events=(0, 0), errors=(0, 0), client_started=False, client_died=False)])

def callback(reply):
    events.append({"category": int(reply.category), "data_hex": bytes(reply.data or b"").hex(),
                   "element_header_hex": bytes(reply.element_header or b"").hex(),
                   "client_swapped": bool(reply.client_swapped)})

try:
    worker = threading.Thread(target=lambda: owner.record_enable_context(ctx, callback), daemon=True)
    worker.start()
    time.sleep(.15)
finally:
    control.record_disable_context(ctx)
    worker.join(2)
    owner.record_free_context(ctx)
print(json.dumps({"context_type": type(ctx).__name__, "reply_count": len(events), "replies": events}))
