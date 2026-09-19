import copy, hashlib, importlib.util, json, pathlib, sys
from bridge import BridgeError, seal, naive_bridge, typed_bridge
HERE=pathlib.Path(__file__).parent
EXPECTED_CORE_BLOB='a16620b65d22757ca9160d68feb1381306cc6ac3'
EXPECTED_CORE_SHA256='268cf282c02f9e2dd38a8c45a36378049443ef2a2431063359011d0552b9c37c'

def load_core():
    spec=importlib.util.spec_from_file_location('core_contract_formal',HERE/'contract.py'); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m); return m

def mk_receipts():
    hint=seal({'receipt_id':'hint-1','role':'HINT','currentness':'HISTORICAL','target_id':'T','point':[120,140],'observation_seq':10,'binding_revision':3,'source_receipt_id':None})
    cur=seal({'receipt_id':'cur-1','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','target_id':'T','point':[420,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':None})
    exact=seal({'receipt_id':'reval-ok','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','target_id':'T','point':[420,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':'hint-1'})
    wrong_source=seal({'receipt_id':'reval-ws','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','target_id':'T','point':[420,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':'hint-X'})
    wrong_target=seal({'receipt_id':'reval-wt','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','target_id':'U','point':[420,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':'hint-1'})
    stale_obs=seal({'receipt_id':'reval-so','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','target_id':'T','point':[420,280],'observation_seq':19,'binding_revision':5,'source_receipt_id':'hint-1'})
    stale_bind=seal({'receipt_id':'reval-sb','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','target_id':'T','point':[420,280],'observation_seq':20,'binding_revision':4,'source_receipt_id':'hint-1'})
    return locals()

def run():
    core=load_core(); dep=(HERE/'contract.py').read_bytes()
    import subprocess
    core_blob=subprocess.check_output(['git','hash-object',str(HERE/'contract.py')],text=True).strip()
    core_sha=hashlib.sha256(dep).hexdigest()
    if core_blob!=EXPECTED_CORE_BLOB or core_sha!=EXPECTED_CORE_SHA256: raise SystemExit('core identity mismatch')
    R=mk_receipts(); current={'observation_seq':20,'binding_revision':5}
    forged=copy.deepcopy(R['hint']); forged['role']='ADMISSION_DEPENDENCY'; forged['currentness']='CURRENT'; forged['observation_seq']=20; forged['binding_revision']=5
    scenarios=[
      ('direct_current',R['cur'],None,current,1,'normal'),
      ('hint_stale_numeric',R['hint'],None,{'observation_seq':10,'binding_revision':3},1,'normal'),
      ('hint_laundered_current_numeric',R['hint'],None,current,1,'normal'),
      ('hint_exact_revalidated',R['hint'],R['exact'],current,1,'normal'),
      ('hint_wrong_source_revalidation',R['hint'],R['wrong_source'],current,1,'normal'),
      ('hint_wrong_target_revalidation',R['hint'],R['wrong_target'],current,1,'normal'),
      ('hint_stale_revalidation_observation',R['hint'],R['stale_obs'],current,1,'normal'),
      ('hint_stale_revalidation_binding',R['hint'],R['stale_bind'],current,1,'normal'),
      ('forged_inplace_role_currentness',forged,None,current,1,'normal'),
      ('direct_current_expired_lease',R['cur'],None,current,20_000_000_000,'normal'),
      ('direct_current_missing_pointer_capability',R['cur'],None,current,1,'missing_pointer'),
    ]
    rows=[]
    for policy in ('naive','typed'):
      for i,(name,evid,reval,override,now_ns,manifest_mode) in enumerate(scenarios):
        mf_caps=[core.INPUT_RELEASE_ALL,core.DISPLAY_GEOMETRY] if manifest_mode=='missing_pointer' else [core.INPUT_POINTER,core.INPUT_RELEASE_ALL,core.DISPLAY_GEOMETRY]
        mf=core.capability_manifest('fake-x11','linux','fake',mf_caps)
        bridge_status='PROGRAM_CONSTRUCTED'; bridge_error=None; program=None
        try:
          if policy=='naive': out=naive_bridge(f'{policy}-{i}',evid,override)
          else: out=typed_bridge(f'{policy}-{i}',evid,reval)
          program=out['program']
        except (BridgeError,KeyError,TypeError,ValueError) as ex:
          bridge_status='BRIDGE_REJECTED'; bridge_error=str(ex)
        adm=None
        if program is not None:
          a=core.admit_program(program,mf,now_ns=now_ns,current_observation_seq=20,current_binding_revision=5)
          adm={'accepted':a.accepted,'error':a.error,'required_capabilities':list(a.required_capabilities)}
        rows.append({'policy':policy,'scenario':name,'bridge_status':bridge_status,'bridge_error':bridge_error,'program':program,'core_admission':adm,'backend_eligible':bool(adm and adm['accepted'])})
    return {'task':'CORE-V1-HINT-LINEAGE-BRIDGE-20260917-001','core_blob':core_blob,'core_sha256':core_sha,'formal_reruns':0,'rows':rows}

if __name__=='__main__': print(json.dumps(run(),sort_keys=True,indent=2))
