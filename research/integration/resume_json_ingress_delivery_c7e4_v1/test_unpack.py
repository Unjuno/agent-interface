import copy, importlib.util, json, pathlib, shutil, subprocess, sys, tempfile
root=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('restore4313',root/'unpack.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
results=[]
for kind in ('existing_destination','missing_part','changed_part','reordered_parts','wrong_archive_digest','wrong_envelope','symlink_part','readable_copy_mismatch'):
    with tempfile.TemporaryDirectory() as td:
        package=pathlib.Path(td)/'package';shutil.copytree(root,package);destination=pathlib.Path(td)/'restored'
        part=package/'capsule/part-00.b64';mp=package/'CAPSULE.json';m=json.loads(mp.read_text())
        if kind=='existing_destination': destination.mkdir()
        elif kind=='missing_part': part.unlink()
        elif kind=='changed_part': part.write_bytes(b'A'+part.read_bytes()[1:])
        elif kind=='reordered_parts': m['parts'][0],m['parts'][1]=m['parts'][1],m['parts'][0];mp.write_text(json.dumps(m))
        elif kind=='wrong_archive_digest': m['archive_sha256']='0'*64;mp.write_text(json.dumps(m))
        elif kind=='wrong_envelope': m['member_files']+=1;mp.write_text(json.dumps(m))
        elif kind=='symlink_part': part.unlink();part.symlink_to(root/'capsule/part-00.b64')
        elif kind=='readable_copy_mismatch': (package/'retained/AUDIT.json').write_text('{}\n')
        try:
            if kind=='readable_copy_mismatch':
                p=subprocess.run([sys.executable,'-B',str(package/'verify_publication.py')],capture_output=True,timeout=8)
                rejected=p.returncode!=0 and b'readable copy differs' in p.stderr
                reason='readable copy differs' if rejected else 'unexpected verifier result'
            else:
                mod.unpack(destination,package); rejected=False;reason='UNEXPECTED_ACCEPT'
        except (ValueError,FileNotFoundError) as e:
            rejected=True;reason=type(e).__name__+': '+str(e).replace(str(pathlib.Path(td)),'<TEMP>')
        results.append({'case':kind,'rejected':rejected,'reason':reason})
result={'decision':'PASS_PACKAGING_REFUSAL_TESTS' if all(x['rejected'] for x in results) else 'FAIL_PACKAGING_REFUSAL_TESTS','checks':len(results),'controls':results,'gui_runs':0,'scientific_reruns':0}
expected=json.loads((root/'PACKAGING_TESTS.json').read_text())
assert result==expected, 'packaging controls changed'
print(json.dumps(result,indent=2));sys.exit(0 if all(x['rejected'] for x in results) else 1)
