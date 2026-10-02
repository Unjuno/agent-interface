import json, time, datetime
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(path):
 try: return open(path).read().strip()
 except Exception as e: return "unavailable:"+str(e)
def snapshot(event, mode, **extra):
 mem={}
 for line in read('/proc/meminfo').splitlines():
  p=line.split(':',1)
  if len(p)==2 and p[0] in ('MemTotal','MemAvailable','SwapTotal','SwapFree'): mem[p[0]]=p[1].strip()
 try: cg=open('/proc/self/cgroup').read().strip().split(':')[-1]
 except Exception: cg='/'
 root='/sys/fs/cgroup'+cg
 state={k:read(root+'/'+k) for k in ('memory.max','memory.current','memory.peak','memory.events','memory.swap.max')}
 state['psi']=read('/proc/pressure/memory')
 print(json.dumps(dict(ts=now(),event=event,mode=mode,meminfo=mem,cgroup=state,**extra)),flush=True)
def main():
 blocks=[]; snapshot('start','pressure',target_mib=640)
 for i in range(80):
  b=bytearray(8*1024*1024)
  for j in range(0,len(b),4096): b[j]=1
  blocks.append(b)
  if (i+1)%4==0 or i==79: snapshot('allocation_step','pressure',allocated_mib=(i+1)*8,steps=i+1)
  time.sleep(.25)
 snapshot('pressure_ready','pressure',allocated_mib=640)
 deadline=time.monotonic()+60
 while time.monotonic()<deadline: time.sleep(.25)
 snapshot('completed','pressure',allocated_mib=640)
if __name__=='__main__':
 try: main()
 except MemoryError:
  snapshot('memory_error','pressure'); raise
