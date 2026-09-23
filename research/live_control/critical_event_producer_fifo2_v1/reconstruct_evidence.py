import base64,hashlib,pathlib,sys
root=pathlib.Path(__file__).parent
s=''.join((root/f'evidence.part0{i}.b64').read_text().strip() for i in (1,2))
data=base64.b64decode(s)
want='22146f5f630e84df5d909fdfa6788dc0422832c5673f6d2baf993915399d8d0a'
got=hashlib.sha256(data).hexdigest()
if got!=want: raise SystemExit(f'SHA mismatch {got}')
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'critical_event_producer_fifo2_v1_evidence.tar.xz')
out.write_bytes(data); print(got, len(data))
