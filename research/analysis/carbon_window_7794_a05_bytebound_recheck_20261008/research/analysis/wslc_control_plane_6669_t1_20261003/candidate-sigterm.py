import json,time,datetime,signal,sys
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(path):
 try:return open(path).read().strip()
 except Exception as e:return 'unavailable:'+str(e)
def snap(event,mode,**extra):
 mem={}
 for line in read('/proc/meminfo').splitlines():
  p=line.split(':',1)
  if len(p)==2 and p[0] in ('MemTotal','MemAvailable','SwapTotal','SwapFree'):mem[p[0]]=p[1].strip()
 try:cg=open('/proc/self/cgroup').read().strip().split(':')[-1]
 except Exception:cg='/'
 root='/sys/fs/cgroup'+cg
 c={k:read(root+'/'+k) for k in ('memory.max','memory.current','memory.peak','memory.events','memory.swap.max')}
 c['psi']=read('/proc/pressure/memory')
 print(json.dumps(dict(ts=now(),event=event,mode=mode,meminfo=mem,cgroup=c,**extra)),flush=True)
def on_term(signum,frame):
 snap('sigterm_received',MODE,signal=signum)
 raise SystemExit(0)
MODE=sys.argv[1]
signal.signal(signal.SIGTERM,on_term)
size=32 if MODE=='control' else 640
blocks=[];snap('start',MODE,target_mib=size)
for i in range(size//8):
 b=bytearray(8*1024*1024)
 for j in range(0,len(b),4096):b[j]=1
 blocks.append(b)
 if (i+1)%4==0 or i+1==size//8:snap('allocation_step',MODE,allocated_mib=(i+1)*8,steps=i+1)
 if MODE=='pressure':time.sleep(.25)
snap('baseline_ready' if MODE=='control' else 'pressure_ready',MODE,allocated_mib=size)
end=time.monotonic()+60
while time.monotonic()<end:time.sleep(.25)
snap('completed',MODE,allocated_mib=size)
