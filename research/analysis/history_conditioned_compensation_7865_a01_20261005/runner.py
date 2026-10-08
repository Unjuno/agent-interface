import argparse,datetime,json,pathlib,subprocess,sys
IMAGE='python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
WSLC=r'C:\Program Files\WSL\wslc.exe'
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=('candidate','audit'));p.add_argument('source_dir');p.add_argument('output_dir');a=p.parse_args();src=pathlib.Path(a.source_dir).resolve();out=pathlib.Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
 names={'candidate':('candidate.raw.json','candidate.stderr','candidate.exit.json'),'audit':('audit.raw.json','audit.stderr','audit.exit.json')}[a.mode];paths=[out/n for n in names]
 if any(x.exists() for x in paths): raise SystemExit('REFUSE_REPLAY: output exists')
 cmd=[WSLC,'run','--rm','--pull','never','--network','none','--cpus','1','--memory','512M','--volume',str(src)+':/src:ro','--volume',str(out)+':/out:ro','--workdir','/src',IMAGE,'python','-B']
 cmd+=['candidate.py','/src/fixture.json'] if a.mode=='candidate' else ['audit.py','/src/fixture.json','/out/candidate.raw.json']
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180);meta={'mode':a.mode,'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':cmd,'exit_code':proc.returncode,'stdout_bytes':len(proc.stdout),'stderr_bytes':len(proc.stderr),'retry_count':0}
 paths[0].write_bytes(proc.stdout);paths[1].write_bytes(proc.stderr);paths[2].write_text(json.dumps(meta,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8');print(json.dumps(meta,sort_keys=True,separators=(',',':')));return proc.returncode
if __name__=='__main__':raise SystemExit(main())
