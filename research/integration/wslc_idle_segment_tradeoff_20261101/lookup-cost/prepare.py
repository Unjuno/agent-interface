import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent
names=('segment.py','test_segment.py','history_baseline.py','bench.py','prepare.py','run.py')
hashes={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
arms=[('segment-r87-a01','ascending'),('segment-r87-a02','descending')]
for ident,order in arms:
    path=root/ident;path.mkdir(exist_ok=False);(path/'output').mkdir()
    c={'allocation':'idle-segment-'+ident,'order':order,'arm_order':arms,'source_sha256':hashes,
       'main_at_freeze':'8ebd9a107a284ea2270f9c846ff163f3f374043f','image':'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25',
       'protocol':'41 alternating order batches of 1024 lookups; deterministic random keys and repeated latest key; elapsed divided by batch size',
       'limitations':'synthetic integer metadata only; not full image reload, end-to-end GUI, threading, overwrite or delete',
       'resources':'private WSLc, one CPU, 1 GiB memory, no network, no pull; swap may not be limited'}
    (path/'conditions.json').write_text(json.dumps(c,indent=2)+'\n')
print('two independent lookup allocations frozen')
