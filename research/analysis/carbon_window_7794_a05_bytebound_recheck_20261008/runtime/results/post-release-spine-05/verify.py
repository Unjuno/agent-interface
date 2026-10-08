"""Verify retained failure evidence, never product acceptance."""
import hashlib,importlib.util,json,pathlib,tarfile,tempfile

def require(ok,why):
    if not ok:raise ValueError(why)

def verify(folder):
    folder=pathlib.Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    archive=folder/'raw.tar.gz'
    require(hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256'],'archive hash')
    with tempfile.TemporaryDirectory() as tmp:
        dest=pathlib.Path(tmp)
        with tarfile.open(archive,'r:gz') as tf:
            members=tf.getmembers()
            require(len(members)==len(manifest['members']) and {m.name for m in members}==set(manifest['members']),'member inventory')
            for m in members:
                require(m.isfile() and not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts,'unsafe member')
                data=tf.extractfile(m).read()
                require(hashlib.sha256(data).hexdigest()==manifest['members'][m.name],'member hash')
                target=dest/m.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        spec=importlib.util.spec_from_file_location('analysis05',dest/'analyze.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=module.analyze(dest)
        require(result==json.loads((dest/'analysis.json').read_text()),'recomputed analysis')
        require(result['status']=='HOLD_PRIMARY_PROTOCOL_DEVIATIONS' and result['matched_comparison'] is False,'failure preserved')
        return {'status':result['status'],'members':len(members),'guarded_exact':3,'direct_exact':0,'scope':'Evidence integrity only; primary deviations, no matched performance comparison or product acceptance.'}

if __name__=='__main__':
    import sys
    print(json.dumps(verify(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).parent),indent=2))
