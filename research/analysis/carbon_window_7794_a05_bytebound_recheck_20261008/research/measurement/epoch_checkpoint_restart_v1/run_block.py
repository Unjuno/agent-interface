import argparse,subprocess,sys,os,json,time

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--result',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--cases',type=int,required=True);a=p.parse_args()
    if os.path.exists(a.db) or os.path.exists(a.result):raise SystemExit('outputs must be absent')
    t=time.perf_counter()
    w=subprocess.run([sys.executable,'writer.py','--db',a.db,'--seed',str(a.seed),'--cases',str(a.cases)],check=True,capture_output=True,text=True)
    # Writer is fully exited before reader subprocess starts.
    r=subprocess.run([sys.executable,'reader.py','--db',a.db,'--out',a.result,'--seed',str(a.seed),'--cases',str(a.cases)],check=True,capture_output=True,text=True)
    meta={'writer_stdout':w.stdout.strip(),'reader_stdout':r.stdout.strip(),'outer_wall_s':time.perf_counter()-t,'writer_returncode':w.returncode,'reader_returncode':r.returncode}
    print(json.dumps(meta,sort_keys=True))
if __name__=='__main__':main()
