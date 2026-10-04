import hashlib,importlib.util,json,os,platform
from pathlib import Path
HERE=Path(__file__).resolve().parent
import test_doom_retained_input_backend_v3 as backend_fixture
spec=importlib.util.spec_from_file_location('direct_analyzer',HERE/'analyze_map01_direct_retained_input_v1.py')
analyzer=importlib.util.module_from_spec(spec); spec.loader.exec_module(analyzer)
raw=json.loads((HERE/'raw-cases.json').read_text(encoding='utf8'))
rows=[]
for case in raw['cases']:
    owner=backend_fixture.Owner(receipt_token=case.get('receipt_token'))
    obj=backend_fixture.make_backend({'Up'},owner,token=case.get('lease_token'))
    obj.raw('Up',False)
    receipt=obj.emitted[0]
    admission={'event':'input_admission','key':'Up','admitted_ns':1,'input_ack_ns':2}
    if case['admission_token_present']: admission['intent_token']=case.get('admission_token')
    result=analyzer.analyze([admission,receipt])
    rows.append({'case':case['case'],'producer_receipt':receipt,'producer_verified':receipt['owner_transition_verified'],'consumer_result':result})
payload={'schema':'map01-v3-backend-direct-analyzer-cross-layer-candidate-I84-v1','backend_source_sha256':hashlib.sha256((HERE/'doom_retained_input_backend_v3.py').read_bytes()).hexdigest(),'backend_test_sha256':hashlib.sha256((HERE/'test_doom_retained_input_backend_v3.py').read_bytes()).hexdigest(),'analyzer_source_sha256':hashlib.sha256((HERE/'analyze_map01_direct_retained_input_v1.py').read_bytes()).hexdigest(),'runtime':{'python':platform.python_version(),'platform':platform.platform(),'uid':os.getuid() if hasattr(os,'getuid') else None,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None,'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None,'src_mountinfo':[line for line in Path('/proc/self/mountinfo').read_text().splitlines() if ' /src ' in line]},'results':rows}
print(json.dumps(payload,indent=2))
