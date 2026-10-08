import json, os, pathlib, signal, sqlite3, subprocess, sys, time
from model import ledger_rows, make_receipt, read_journal, digest
ROOT=pathlib.Path(__file__).parent

def run(case_id,policy,outdir):
    out=pathlib.Path(outdir); out.mkdir(parents=True,exist_ok=False)
    journal=str(out/'journal.jsonl'); ledger=str(out/'ledger.sqlite')
    rfd,wfd=os.pipe()
    p=subprocess.Popen([sys.executable,str(ROOT/'writer.py'),'--case',case_id,'--policy',policy,'--journal',journal,'--ledger',ledger,'--control-fd',str(wfd)],pass_fds=(wfd,),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    os.close(wfd)
    with os.fdopen(rfd) as rf:
        marker=json.loads(rf.readline())
    before=ledger_rows(ledger)
    if policy=='post_fsync_sigkill':
        os.kill(p.pid,signal.SIGKILL); p.wait(timeout=5)
    else:
        p.wait(timeout=5)
    stdout=p.stdout.read(); stderr=p.stderr.read()
    after_writer=ledger_rows(ledger)
    rec1=subprocess.run([sys.executable,str(ROOT/'recover.py'),'--journal',journal,'--ledger',ledger],capture_output=True,text=True,check=True)
    rec2=subprocess.run([sys.executable,str(ROOT/'recover.py'),'--journal',journal,'--ledger',ledger],capture_output=True,text=True,check=True)
    mut=subprocess.run([sys.executable,str(ROOT/'recover.py'),'--journal',journal,'--ledger',ledger,'--mutate'],capture_output=True,text=True,check=True)
    result={'case_id':case_id,'policy':policy,'marker':marker,'writer_returncode':p.returncode,'writer_stdout':stdout,'writer_stderr':stderr,'ledger_before_kill':before,'ledger_after_writer':after_writer,'recovery1':json.loads(rec1.stdout),'recovery2':json.loads(rec2.stdout),'mutated_recovery':json.loads(mut.stdout),'journal':read_journal(journal),'final_ledger':ledger_rows(ledger),'release_retry_count':0,'task_action_count':0}
    (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1],sys.argv[2],sys.argv[3]),sort_keys=True))
