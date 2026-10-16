"""Unpromoted desktop entrypoint for shared session_v9 pointer programs."""
import argparse,copy,contextlib,hashlib,json,shutil,sys,threading,time
from pathlib import Path
from session_v16 import Backend,suite,SERVO_SCHEMA
from executor_v3 import Executor
from lease import Expired
from presentation_v2 import Presentation
from delivery_ledger_v2 import DeliveryLedger
from receipt_journal import ReceiptJournal
from finalization_v3 import finalize
from saved_effect import inspect_saved_cells
from effect_checkpoint import Checkpoints
from request_correlation_v2 import correlation
from admitted_lineage import AdmittedLineage
from timing_clock import describe as describe_clock
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--app',choices=suite.APPS,required=True)
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--chromium',default='/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome')
    ap.add_argument('--presentation',choices=['full','compact'],default='full')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    clock_identity=describe_clock()
    (args.out/'timing-clock.json').write_text(json.dumps(clock_identity,indent=2)+'\n')
    final_status=None;final_id=None;final_thread=None;final_done=threading.Event()
    lineage=AdmittedLineage();lock=threading.Lock();events=[];projection=Presentation();ledger=DeliveryLedger()
    def emit(record):
        record=lineage.attach(record)
        record['clock_domain_id']=clock_identity['domain_id']
        output_flushed=True
        try:
            with lock:
                record['emit_started_ns']=time.perf_counter_ns();events.append(record)
                line=json.dumps(record)
                with (args.out/'events.jsonl').open('a') as log:log.write(line+'\n')
                visible=projection.project(record) if args.presentation=='compact' else [record]
                for item in visible:
                    item=ledger.prepare(item)
                    rendered=json.dumps(item)
                    with (args.out/'delivered.jsonl').open('a') as delivery:delivery.write(rendered+'\n')
                    started=time.perf_counter_ns()
                    try:print(rendered,flush=True)
                    except BrokenPipeError:output_flushed=False
                    else:
                        receipt=ledger.flushed(item,len((rendered+'\n').encode('utf-8')),started)
                        journal.append(receipt)
        finally:
            if record.get('event')=='terminal' and record.get('id')==final_id:final_done.set()
        return output_flushed
    checkpoints=Checkpoints(emit)
    with (args.out/'delivery-flush.jsonl').open('xb') as receipt_stream:
        journal=ReceiptJournal(receipt_stream)
        session=None;server=None;engine=None;output=None;backend=None
        try:
            hashes={}
            for path in [HERE/'interactive_v29.py',HERE/'effect_checkpoint.py',HERE/'timing_clock.py',HERE/'finalization_v3.py',HERE/'saved_effect.py',HERE/'request_correlation_v2.py',HERE/'admitted_lineage.py',HERE/'receipt_journal.py',HERE/'delivery_ledger_v2.py',HERE/'presentation_v2.py',HERE/'session_v16.py',HERE/'patch_servo.py',HERE/'visual_anchor.py',HERE/'session_v15.py',HERE/'session_v13.py',HERE/'session_v12.py',HERE/'session_v11.py',HERE/'input_owner_v9.py',HERE/'pointer_reply_v2.py',HERE/'session_v9.py',HERE/'input_owner_v5.py',HERE/'presentation.py',HERE/'session_v8.py',HERE/'quiet_window.py',HERE/'session_v7.py',HERE/'session_v6.py',HERE/'input_owner_v2.py',HERE/'session_v5.py',HERE/'input_owner.py',HERE/'executor_v3.py',HERE/'session_v4.py',HERE/'lease.py',HERE.parent/'observation_tiles/tile_transport.py',
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
            emit(dict(event='ready',app=args.app,task=task,goal=goal,presentation=args.presentation,finish_after_contract='submit finish_after=true reserves final program; after terminal close input admission and score; cancel/clock remain available; finish cleans up without rescoring',basic_step_examples=[{'op':'text','text':'123'},{'op':'key','key':'Return'},{'op':'chord','modifier':'Control_L','key':'s'}],decision_evidence_schema={'required_for':'submit','fields':{'delivery_id':'successfully flushed observation or review delivery ID','observation_sequence':'must equal expected_sequence','producer':['assistant','scripted','human']},'authority':'none; ordinary admission required'},servo_schema=SERVO_SCHEMA,operations=['submit','pointer_reply','cancel','clock','finish','finalization_status','effect_checkpoint'],guided_fields=['points','duration_ms','reply_timeout_ms','max_updates','feedback_delay_ms'],reply_fields=['ticket','sequence','command']))
            backend.snapshot('initial',0)
            request_sequence=0
            for line in sys.stdin:
                request_sequence+=1;command=None
                try:
                    command=json.loads(line);emit(dict(event='command',command=command,received_ns=time.perf_counter_ns(),**correlation(request_sequence,command)))
                    if not isinstance(command,dict):raise ValueError('command object required')
                    if command['op']=='submit':
                        with lock:
                            evidence=ledger.validate(command['decision_evidence'])
                        if command['decision_evidence']['observation_sequence']!=command['expected_sequence']:raise ValueError('evidence/expected sequence mismatch')
                        emit(dict(evidence,id=command['id'],received_ns=time.perf_counter_ns()))
                        if final_id is not None:raise ValueError('final program already reserved')
                        finish_after=command.get('finish_after',False)
                        if type(finish_after) is not bool:raise ValueError('finish_after must be boolean')
                        if finish_after:final_id=command['id']
                        try:
                            lineage.begin(command['id'],correlation(request_sequence,command))
                            try:engine.submit(command['id'],command['steps'],command['expected_sequence'],command['valid_until_ns'])
                            finally:lineage.end()
                        except Exception:
                            if finish_after:final_id=None
                            raise
                        if finish_after:
                            def finalize_episode():
                                nonlocal final_status
                                final_done.wait()
                                observe_effect=(lambda:inspect_saved_cells(output,action_id=final_id,expected={'A1':goal['a'],'A2':goal['b']},observation_closed=True)) if args.app=='calc' else None
                                outcome=finalize(final_id,engine.close,lambda:suite.evaluate(args.app,output,goal),emit,observe_effect=observe_effect)
                                with lock:final_status=copy.deepcopy(outcome)
                                try:suite.write_json(args.out/'finalization-status.json',outcome)
                                except Exception as exc:print(json.dumps(dict(event='finalization_status_write_failed',error=repr(exc),outcome=outcome)),file=sys.stderr,flush=True)
                            final_thread=threading.Thread(target=finalize_episode,daemon=True);final_thread.start()
                    elif command['op']=='pointer_reply':emit(dict(event='reply_accepted',**backend.reply_pointer(command['ticket'],command['sequence'],command['command'])))
                    elif command['op']=='cancel':engine.cancel(command['id'])
                    elif command['op']=='clock':emit(dict(event='clock',runtime_ns=time.perf_counter_ns(),sequence=backend.sequence))
                    elif command['op']=='effect_checkpoint':
                        contract=command['contract']
                        if not isinstance(contract,dict) or set(contract)!={'kind','expected'}:raise ValueError('explicit artifact contract required')
                        if args.app=='chromium' and contract['kind']=='saved_form_value':
                            if not isinstance(contract['expected'],str):raise ValueError('expected form value must be a string')
                        elif args.app=='calc' and contract['kind']=='saved_cells':
                            if not isinstance(contract['expected'],dict) or not contract['expected']:raise ValueError('expected cell mapping required')
                        else:raise ValueError('contract unsupported for application')
                        checkpoints.request(output,contract,correlation(request_sequence,command))
                    elif command['op']=='finalization_status':
                        with lock:status_snapshot=copy.deepcopy(final_status)
                        emit(dict(event='finalization_status',state='available' if status_snapshot is not None else ('pending' if final_id is not None else 'not_requested'),outcome=status_snapshot,scope='read-only retained result; no rescore or new authority',**correlation(request_sequence,command)))
                    elif command['op']=='finish':
                        if final_thread is not None:final_thread.join()
                        else:
                            engine.close()
                            emit(dict(event='independent_evaluation',**suite.evaluate(args.app,output,goal)))
                        break
                    else:raise ValueError('unsupported command')
                except (ValueError,KeyError,TypeError,Expired) as exc:
                    emit(dict(event='rejected',reason=str(exc),**correlation(request_sequence,command)))
        finally:
            checkpoints.close()
            if engine is not None:engine.close()
            if final_thread is not None:final_thread.join()
            if backend is not None:
                try:backend.close()
                finally:suite.write_json(args.out/'owner-events.json',backend.owner.records)
            if output is not None and output.exists():shutil.copy2(output,args.out/output.name)
            if server is not None:server.shutdown();server.server_close()
            if session is not None:session.close();shutil.rmtree(session.tmp)


if __name__=='__main__':main()
