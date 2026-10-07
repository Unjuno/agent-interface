import json, time, pathlib, platform, sys, datetime
P=pathlib.Path

def counters():
    def read(path):
        try: return P(path).read_text().strip()
        except OSError: return None
    return {'schedstat':read('/proc/self/schedstat'), 'cpu_stat':read('/sys/fs/cgroup/cpu.stat'), 'cpu_max':read('/sys/fs/cgroup/cpu.max'), 'process_cpu_ns':time.process_time_ns()}

def main():
    out=P(sys.argv[1]); out.mkdir(exist_ok=False)
    meta={'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'clock':vars(time.get_clock_info('monotonic')),'before':counters(),'order':['sleep','spin1','spin15','spin15','spin1','sleep'],'period_ns':20000000,'per_block':32}
    with (out/'raw.jsonl').open('x') as f:
        for block,arm in enumerate(meta['order']):
            start=time.monotonic_ns(); spin={'sleep':0,'spin1':1000000,'spin15':15000000}[arm]
            for i in range(32):
                deadline=start+(i+1)*20000000
                before=counters(); entry=time.monotonic_ns()
                remaining=deadline-spin-time.monotonic_ns()
                if remaining>0: time.sleep(remaining/1e9)
                wake=time.monotonic_ns()
                while time.monotonic_ns()<deadline: pass
                observed=time.monotonic_ns(); after=counters()
                row={'block':block,'arm':arm,'i':i,'block_start_ns':start,'deadline_ns':deadline,'entry_ns':entry,'sleep_return_ns':wake,'observed_ns':observed,'lateness_ns':observed-deadline,'before':before,'after':after}
                f.write(json.dumps(row,sort_keys=True)+'\n'); f.flush()
    meta['after']=counters(); meta['utc_end']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (out/'environment.json').write_text(json.dumps(meta,indent=2)+'\n')
if __name__=='__main__': main()
