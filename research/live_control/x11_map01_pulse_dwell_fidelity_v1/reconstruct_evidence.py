import base64, hashlib, pathlib, sys
HERE=pathlib.Path(__file__).resolve().parent
parts=sorted(HERE.glob('evidence.part*.b64'))
data=base64.b64decode(''.join(p.read_text().strip() for p in parts))
want='6fd98e81baa44fd368d7343510e7b21d9f2091c8996f883dfe7901dcfc536e2a'
got=hashlib.sha256(data).hexdigest()
if got!=want: raise SystemExit(f'SHA mismatch: {got} != {want}')
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'x11_map01_pulse_dwell_fidelity_v1_evidence.tar.xz')
out.write_bytes(data); print(f'{out} {len(data)} bytes sha256={got}')
