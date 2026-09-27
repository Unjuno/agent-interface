"""Private renderer/capture process; no XTEST, keyboard, mouse or task action."""
from __future__ import annotations
import base64, hashlib, json, os, sys, time
from native_io import Native
import legacy_transport as legacy

def main() -> None:
    n=Native(sys.argv[1])
    try:
        print(json.dumps({'event':'ready','pid':os.getpid()}),flush=True)
        for line in sys.stdin.buffer:
            request=json.loads(line); op=request['op']
            if op=='paint': result=n.paint(request['count'])
            elif op=='capture':
                data,clocks=n.capture()
                meta={'case_id':request['case_id'],'seq':1,
                      'capture_start_ns':clocks['native'][1],'capture_end_ns':clocks['native'][2],
                      'python_return_ns':clocks['after_py_ns'],'serialize_start_ns':time.monotonic_ns(),
                      'pixel_sha256':hashlib.sha256(data).hexdigest()}
                if request.get('bad_digest'): meta['pixel_sha256']='f'*64
                if request.get('wrong_id'): meta['case_id']+='-other'
                packet=legacy.encode(meta,data)
                result={'packet_b64':base64.b64encode(packet).decode(),'capture':clocks}
            elif op=='quit':
                print(json.dumps({'op':op,'result':{'stopped':True},'pid':os.getpid()}),flush=True)
                break
            else: raise ValueError('unsupported fixture operation')
            print(json.dumps({'op':op,'result':result,'pid':os.getpid()},separators=(',',':')),flush=True)
    finally: n.close()
if __name__=='__main__': main()
