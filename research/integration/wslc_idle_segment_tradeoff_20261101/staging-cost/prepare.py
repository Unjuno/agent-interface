import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent
names=('segment.py','test_segment.py','history_baseline.py','bench.py','prepare.py','run.py')
hashes={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
arms=[('segment-r86-a01','ascending'),('segment-r86-a02','descending')]
for ident,order in arms:
    path=root/ident;path.mkdir(exist_ok=False);(path/'output').mkdir()
    conditions={'allocation':'idle-segment-'+ident,'order':order,'arm_order':arms,'source_sha256':hashes,
        'baseline_pr':'#10074 at 0675ab810f7ee890d0904b8a402678c81f8dbafb','main_at_freeze':'8ebd9a107a284ea2270f9c846ff163f3f374043f',
        'image':'sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25',
        'protocol':'41 alternating paired trials each size; time includes fork, append and immediate staged-object disposal; separate tracemalloc peak',
        'sizes':[0,1000,10000,100000],'candidate':'256-entry immutable blocks; append-only increasing positive integer keys',
        'limitations':'synthetic metadata and shared 16x16 image; no GUI/capture/model; no overwrite, delete, general mapping or artifact reload; no hard timing claim',
        'resources':'private WSLc container, 1 CPU, 1 GiB memory, no network, no pull; swap may not be limited'}
    (path/'conditions.json').write_text(json.dumps(conditions,indent=2)+'\n')
print('two independent allocations frozen')
