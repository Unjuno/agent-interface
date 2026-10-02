import json,time,datetime
def snap(event):
 m={}
 for line in open('/proc/meminfo'):
  p=line.split(':',1)
  if len(p)==2 and p[0] in ('MemTotal','MemAvailable'):m[p[0]]=p[1].strip()
 print(json.dumps({'ts':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,'mode':'no_pressure_control','allocated_mib':32,'meminfo':m}),flush=True)
b=bytearray(32*1024*1024)
for i in range(0,len(b),4096):b[i]=1
snap('baseline_ready')
end=time.monotonic()+60
while time.monotonic()<end:time.sleep(.25)
snap('completed')
