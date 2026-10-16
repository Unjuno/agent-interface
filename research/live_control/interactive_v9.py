"""Interactive revision 5: explicit lifecycle for the independent input owner."""
import argparse,contextlib,hashlib,json,shutil,sys,threading,time
from pathlib import Path
from session_v8 import Backend,suite
from executor_v3 import Executor
from lease import Expired
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--app',choices=suite.APPS,required=True)
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--chromium',default='/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    lock=threading.Lock();events=[]
    def emit(record):
        with lock:
            record['emit_started_ns']=time.perf_counter_ns();events.append(record)
            line=json.dumps(record)
            with (args.out/'events.jsonl').open('a') as log:log.write(line+'\n')
            try:print(line,flush=True)
            except BrokenPipeError:pass
    session=None;server=None;engine=None;output=None;backend=None
    try:
        hashes={}
        for path in [HERE/'interactive_v9.py',HERE/'session_v8.py',HERE/'quiet_window.py',HERE/'session_v7.py',HERE/'session_v6.py',HERE/'input_owner_v2.py',HERE/'session_v5.py',HERE/'input_owner.py',HERE/'executor_v3.py',HERE/'session_v4.py',HERE/'lease.py',HERE.parent/'observation_tiles/tile_transport.py',
                     HERE.parent/'observation_tiles/image_artifact.py',HERE.parent/'observation_gating/gui_suite.py',
                     HERE.parent/'observation_gating/exact_gate.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py']:
            hashes[str(path.relative_to(HERE.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
        suite.write_json(args.out/'sources.json',hashes)
        # Xlib emits setup diagnostics to stdout. Keep the control lane JSON-only.
        # This redirect ends before the executor thread starts.
        with (args.out/'setup-diagnostics.txt').open('w') as diagnostics, contextlib.redirect_stdout(diagnostics):
            session=suite.Session();goal,output,server=suite.prepare(session,args.app,args.seed,args.chromium)
            backend=Backend(session,args.out,emit)
        engine=Executor(backend,emit)
        task={'xterm':'Type token and Return; saved text must equal token.', 'calc':'Enter a in A1 and b in A2, then save sheet.xlsx in Excel format.', 'chromium':'Submit token in the form.', 'inkscape':'Move the red rectangle right while preserving its size and vertical position.'}[args.app]
        emit(dict(event='ready',app=args.app,task=task,goal=goal,operations=['submit','cancel','clock','finish']))
        backend.snapshot('initial',0)
        for line in sys.stdin:
            try:
                command=json.loads(line);emit(dict(event='command',command=command,received_ns=time.perf_counter_ns()))
                if command['op']=='submit':engine.submit(command['id'],command['steps'],command['expected_sequence'],command['valid_until_ns'])
                elif command['op']=='cancel':engine.cancel(command['id'])
                elif command['op']=='clock':emit(dict(event='clock',runtime_ns=time.perf_counter_ns(),sequence=backend.sequence))
                elif command['op']=='finish':
                    engine.close()
                    emit(dict(event='independent_evaluation',**suite.evaluate(args.app,output,goal)))
                    break
                else:raise ValueError('unsupported command')
            except (ValueError,KeyError,TypeError,Expired) as exc:
                emit(dict(event='rejected',reason=str(exc)))
    finally:
        if engine is not None:engine.close()
        if backend is not None:
            try:backend.close()
            finally:suite.write_json(args.out/'owner-events.json',backend.owner.records)
        if output is not None and output.exists():shutil.copy2(output,args.out/output.name)
        if server is not None:server.shutdown();server.server_close()
        if session is not None:session.close();shutil.rmtree(session.tmp)


if __name__=='__main__':main()
