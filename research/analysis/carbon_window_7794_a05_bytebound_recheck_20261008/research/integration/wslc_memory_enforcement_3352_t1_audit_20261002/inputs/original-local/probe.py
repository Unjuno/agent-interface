import pathlib,time,sys
print("cgroup",pathlib.Path("/proc/self/cgroup").read_text().strip())
print("memory.max",pathlib.Path("/sys/fs/cgroup/memory.max").read_text().strip())
n=int(sys.argv[1]); b=bytearray(n*1024*1024)
for i in range(0,len(b),4096): b[i]=1
print(f"ALLOCATED_MIB={n}",flush=True)
time.sleep(1)
