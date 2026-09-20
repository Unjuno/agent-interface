from __future__ import annotations
import json,re,sys
from pathlib import Path
texts=[Path(p).read_text() for p in sys.argv[1:]]
s='\n'.join(texts)
fq=re.search(r'CNTFRQ_EL0=(\d+)',s)
rows=[]
for m in re.finditer(r'sample=(\d+) status=ok monotonic_ns=(\d+) cntvct_delta=(\d+) pmccntr_delta=(\d+)',s):
    i,mono,cnt,pmu=map(int,m.groups())
    rows.append({'sample':i,'monotonic_ns':mono,'cntvct_delta':cnt,'pmccntr_delta':pmu,
      'cntvct_hz':cnt*1e9/mono if mono else None,'pmccntr_hz':pmu*1e9/mono if mono else None})
freqs=[r['pmccntr_hz'] for r in rows if r['pmccntr_hz']]
decision='PASS_HIGH_RESOLUTION_COUNTER_AVAILABLE' if len(rows)==5 and min(freqs)>=1e9 else 'STOP_NO_VALID_COUNTER_RESULT'
if 'SIGILL_PMU_READ' in s: decision='STOP_PMU_ACCESS_SIGILL'
if 'unexpected EOF' in s or 'docker API' in s: decision='STOP_RUNTIME_DISCONNECTED_DURING_PREFLIGHT'
out={'schema':'issue3453-construction-clock51-audit-v1','decision':decision,'formal_allocation':False,
 'cntfrq_hz':int(fq.group(1)) if fq else None,'rows':rows,'sample_count':len(rows),
 'runtime_recovered_noop':any('29.4.0 linux/aarch64' in x for x in texts),
 'pmccntr_hz_min':min(freqs) if freqs else None,'pmccntr_hz_max':max(freqs) if freqs else None,
 'limitations':['A counter-resolution PASS would not bound scorer getter-call duration or instrumentation scheduling effects.',
 'No game or formal allocation ran; no phase observation is claimed.']}
print(json.dumps(out,indent=2,sort_keys=True))
