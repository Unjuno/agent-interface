"""Read-only focus subscription plus XGetImage source. No scenario input."""
import base64, hashlib, json, os, sys, time
from Xlib import X, display

def emit(o): print(json.dumps(o,sort_keys=True,separators=(',',':')),flush=True)

def main():
    d = display.Display(); seq = {}; windows = {}; sessions = {}
    try:
        emit({'ready':True,'pid':os.getpid()})
        for line in sys.stdin:
            c = json.loads(line); op = c['op']
            if op == 'configure':
                sessions = c['sessions']; seq = {v:0 for v in sessions.values()}
                windows = {k:d.create_resource_object('window',v) for k,v in c['windows'].items()}
                windows['A'].change_attributes(event_mask=X.FocusChangeMask); d.sync()
                emit({'configured':True, 'mask':windows['A'].get_attributes().your_event_mask})
            elif op == 'drain':
                d.sync(); raw = []; records = []
                while d.pending_events():
                    e = d.next_event(); now = time.monotonic_ns()
                    r = {'type':e.type,'window':e.window.id,'mode':e.mode,'detail':e.detail,
                         'send_event':bool(e.send_event),'sequence_number':e.sequence_number,
                         'observed_ns':now}
                    raw.append(r)
                    if e.type not in (X.FocusIn, X.FocusOut) or e.window.id != windows['A'].id \
                       or e.mode != X.NotifyNormal or e.detail != X.NotifyNonlinear or e.send_event:
                        raise ValueError('unexpected native event')
                    s = sessions['A']; seq[s] += 1
                    records.append({'session':s,'seq':seq[s],
                        'kind':'FOCUS_RESTORED' if e.type == X.FocusIn else 'FOCUS_LOST','evidence':r})
                emit({'raw_events':raw,'records':records})
            elif op == 'capture':
                name = c['target']; w = windows[name]; start = time.monotonic_ns()
                im = w.get_image(0,0,32,32,X.ZPixmap,0xffffffff)
                end = time.monotonic_ns(); data = (im.data.encode('latin-1') if isinstance(im.data,str) else bytes(im.data))
                if im.depth != 24 or len(data) != 4096: raise ValueError('pixel ABI')
                s = sessions[name]; seq[s] += 1
                emit({'record':{'session':s,'seq':seq[s],'kind':'STATE','evidence':{
                    'window':w.id,'depth':im.depth,'capture_start_ns':start,'capture_end_ns':end,
                    'pixels_b64':base64.b64encode(data).decode(),'sha256':hashlib.sha256(data).hexdigest()}}})
            elif op == 'close':
                emit({'closed':True}); return
            else: raise ValueError('op')
    finally: d.close()
if __name__ == '__main__': main()
