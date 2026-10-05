"""One official saved-only container launch, strictly after native terminal0."""
import argparse
from pathlib import Path
import hashlib
from runner import receipt,write
import reference as ref

def admit_audit_state(state,f,exit_code):
    exit_code=ref.integer(exit_code)
    ref.integer(state['State']['ExitCode'])
    h=state['HostConfig']
    ref.need(state['State']['Status']=='exited' and state['State']['ExitCode']==exit_code,'audit terminal identity')
    ref.need(exit_code==0,'saved auditor terminal0')
    for k in ('Running','Paused','Restarting','OOMKilled','Dead'):ref.need(state['State'][k] is False,'audit terminal '+k)
    ref.need(ref.integer(state['RestartCount'])==0,'audit restart0')
    ref.join(state['Image'],f['image_id'],'audit image')
    ref.join(state['Config']['User'],'501:501','audit nonroot')
    ref.join(state['Config']['Cmd'],f['audit_native_argv'],'audit native argv')
    ref.join({'Entrypoint':state['Config']['Entrypoint'],**{k:h[k] for k in ('Runtime','Privileged','CapAdd','Tmpfs')}},f['effective_runtime'],'audit effective runtime')
    ref.join({k:h[k] for k in ('NanoCpus','Memory','MemorySwap','PidsLimit','NetworkMode','ReadonlyRootfs','CapDrop','SecurityOpt')},
             {'NanoCpus':1000000000,'Memory':536870912,'MemorySwap':536870912,'PidsLimit':64,'NetworkMode':'none',
              'ReadonlyRootfs':True,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges']},'audit effective isolation')
    actual={}
    for m in state['Mounts']:
        ref.need(m['Type']=='bind' and type(m['RW']) is bool and m['Destination'] not in actual,'unique audit bind')
        actual[m['Destination']]=(m['Source'],m['RW'])
    ref.join(actual,{'/src':(f['guest_source'],False),'/raw':(f['guest_wrapper'],False),'/out':(f['guest_audit'],True)},'three closed audit mounts')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',type=Path,required=True)
    a=ap.parse_args();f=ref.read(a.freeze);out=Path(f['host_audit']);raw=Path(f['host_raw'])
    from audit_commands import admit_audit_commands,admit_freeze_bytes
    admit_audit_commands(f)
    here=Path(__file__).resolve().parent
    from protocol import freeze_filename
    freeze_file=freeze_filename(f['mode'],f.get('freeze_file'))
    admit_freeze_bytes(a.freeze.read_bytes(),(here/freeze_file).read_bytes())
    from evidence import admit_launch,admit_transport
    from mount_adapter import normalize_launch,guard_output
    guard_output(raw,out,Path(__file__).resolve().parent)
    launch=ref.read(raw/'launch.json')
    admit_launch(normalize_launch(launch,f),f)
    admit_transport(ref.read(raw/'consumed.json'),launch,ref.read(raw/'copy.json'),ref.read(raw/'post_source.json'),f)
    ref.need(ref.read(raw/'record/raw.json')['status']=='COMPLETE','native complete prerequisite')
    out.mkdir(exist_ok=False)
    from tree_custody import host_manifest,guest_manifest,assert_manifest
    def probe(root,label):
        folder=out/('probe-'+label);folder.mkdir(exist_ok=False)
        return guest_manifest(root,lambda index,value:write(folder/(str(index)+'.json'),value))
    host_raw=host_manifest(raw);write(out/'host-raw-manifest.json',host_raw)
    staged=receipt(f['audit_stage_command']);write(out/'staging.json',staged)
    ref.need(staged['exit_code']==0,'stage full immutable raw wrapper')
    staged_raw,receipts=probe(f['guest_wrapper'],'pre-raw');write(out/'pre-raw-custody.json',receipts)
    assert_manifest(staged_raw,host_raw,'host to guest full raw identity')
    source_names=list(f['source_sha256'])+[freeze_file]
    if f['mode']=='formal':source_names.append('readiness-RESULT.json')
    host_source={n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in source_names}
    guest_source,receipts=probe(f['guest_source'],'pre-source');write(out/'pre-source-custody.json',receipts)
    assert_manifest(guest_source,host_source,'audit staged source identity')
    mkdir=receipt(f['audit_mkdir_command']);write(out/'mkdir.json',mkdir)
    ref.need(mkdir['exit_code']==0,'exclusive audit output')
    result=receipt(f['auditor_command']);write(out/'launch.json',result)
    inspection=receipt(f['audit_inspect_command']);write(out/'inspection.json',inspection)
    copied=receipt(f['audit_copy_command']);write(out/'copy.json',copied)
    guest_result=None
    if ref.integer(result['exit_code'])==0 and ref.integer(copied['exit_code'])==0:
        guest_result,result_receipts=probe(f['guest_audit']+'/result','guest-result')
        write(out/'guest-result-custody.json',result_receipts)
    post_raw,receipts=probe(f['guest_wrapper'],'post-raw');write(out/'post-raw-custody.json',receipts)
    assert_manifest(post_raw,host_raw,'guest raw unchanged after audit')
    assert_manifest(host_manifest(raw),host_raw,'host raw unchanged after audit')
    post_source,receipts=probe(f['guest_source'],'post-source');write(out/'post-source-custody.json',receipts)
    assert_manifest(post_source,host_source,'guest source unchanged after audit')
    ref.need(ref.integer(result['exit_code'])==0 and ref.integer(copied['exit_code'])==0,
             'first saved auditor or copy failure retained; do not retry')
    assert_manifest(host_manifest(out/'result'),guest_result,'guest to host full audit result identity')
    ref.need(ref.integer(inspection['exit_code'])==0 and ref.integer(copied['exit_code'])==0,'inspection/copy terminal0')
    admit_audit_state(ref.parse_record(inspection['stdout']),f,result['exit_code'])
    write(out/'admission.json',{'status':'PASS_AUDIT_CUSTODY_SCOPED','native_producer_invocations':0,
                              'saved_auditor_invocations':1,'result_sha256':guest_result['RESULT.json'],
                              'freeze_sha256':hashlib.sha256(a.freeze.read_bytes()).hexdigest()})

if __name__=='__main__':main()
