import json, os, tempfile, threading, time
from dataclasses import dataclass
from pathlib import Path
from map01_telemetry_session_v2 import (
    CommandStopState, make_v12_command_handler_v2,
    run_telemetry_control_loop_v2, validate_terminal_score_agreement,
)

@dataclass(frozen=True)
class Sample:
    sample_ns:int; kill_count:int; death_count:int; episode_finished:bool; player_dead:bool; map_exit:bool
    def as_dict(self):
        return {"sample_ns":self.sample_ns,"kill_count":self.kill_count,"death_count":self.death_count,"episode_finished":self.episode_finished,"player_dead":self.player_dead,"map_exit":self.map_exit}
class Game:
    def __init__(self): self.finished=False; self.dead=False; self.kills=0; self.deaths=0
class Scorer:
    def __init__(self,g,out):
        self.g=g; self.owner=threading.get_ident(); self.rows=[]; self.out_dir=Path(out); self.summary_path=self.out_dir/'summary.json'
    def sample(self):
        if threading.get_ident()!=self.owner: raise RuntimeError('owner thread changed')
        return Sample(time.perf_counter_ns(),self.g.kills,self.g.deaths,self.g.finished,self.g.dead,self.g.finished and not self.g.dead)
    def sink(self,r): self.rows.append(dict(r))
    def write_summary(self,stats):
        row={"schema":"base","samples":stats.samples,"commands":stats.commands,"owner_thread_id":stats.owner_thread_id,"scorer_records":len(self.rows)}
        self.summary_path.write_text(json.dumps(row)); return row
class Executor:
    def __init__(self): self.calls=[]
    def submit(self,*a): self.calls.append(('submit',a))
    def cancel(self,*a): self.calls.append(('cancel',a))
class Backend: sequence=9

def run(commands, finish_mutation=lambda g:None, save_mutation=None, score_override=None):
    rd,wr=os.pipe(); os.write(wr,''.join(json.dumps(c)+'\n' for c in commands).encode()); os.close(wr)
    with tempfile.TemporaryDirectory() as d:
        g=Game(); scorer=Scorer(g,d); emitted=[]; state=CommandStopState(); score={}
        def on_finish():
            finish_mutation(g)
            score.update({"map_exit":g.finished and not g.dead,"episode_finished":g.finished,"player_dead":g.dead,"death_count":g.deaths,"kill_count":g.kills})
            if score_override: score.update(score_override)
        handler=make_v12_command_handler_v2(emit=emitted.append,executor=Executor(),backend=Backend(),on_finish=on_finish,stop_state=state,on_save_fixture=None if save_mutation is None else lambda:save_mutation(g))
        result=run_telemetry_control_loop_v2(fd=rd,scorer=scorer,command_handler=handler,stop_state=state,sample_hz=35,terminal_score_fn=lambda:dict(score))
        final_blob=(Path(d)/'independent-scorer-final.json').read_text() if (Path(d)/'independent-scorer-final.json').exists() else None
        summary_blob=scorer.summary_path.read_text(); os.close(rd)
        return g,scorer,emitted,state,result,final_blob,summary_blob

def test_finish_records_exactly_one_post_finish_sample_and_agrees():
    g,s,e,state,(stats,summary,final),blob,_=run([{"op":"finish"}],lambda g:(setattr(g,'kills',2),setattr(g,'finished',True)))
    assert stats.samples==1 and len(s.rows)==2
    assert state.reason=='finish' and summary['post_finish_final_sample'] is True
    assert summary['terminal_score_agreement']['agreement'] is True
    assert final['sample']['kill_count']==2 and final['sample']['map_exit'] is True
    assert json.loads(blob)['controller_visible'] is False

def test_finish_disagreement_fails_closed():
    try:
        run([{"op":"finish"}],lambda g:setattr(g,'finished',True),score_override={'map_exit':False})
    except ValueError as exc:
        assert 'terminal scorer disagreement' in str(exc)
    else: raise AssertionError('disagreement accepted')

def test_save_fixture_stops_without_final_scorer_record():
    g,s,e,state,(stats,summary,final),blob,_=run([{"op":"save_fixture"}],save_mutation=lambda g:setattr(g,'finished',True))
    assert state.reason=='save_fixture' and final is None and blob is None
    assert len(s.rows)==1 and summary['post_finish_final_sample'] is False

def test_rejected_command_is_nonterminal_then_finish_closes():
    g,s,e,state,(stats,summary,final),_,_=run([{"op":"unknown"},{"op":"finish"}],lambda g:setattr(g,'finished',True))
    assert stats.commands==2 and state.reason=='finish' and final is not None
    assert [x['event'] for x in e].count('rejected')==1

def test_score_validator_is_type_strict():
    sample=Sample(1,0,0,True,False,True)
    try:
        validate_terminal_score_agreement(sample,{"map_exit":1,"episode_finished":True,"player_dead":False,"death_count":0,"kill_count":0})
    except ValueError: pass
    else: raise AssertionError('bool/int alias accepted')

def test_controller_stream_contains_no_scorer_payload():
    g,s,e,state,(stats,summary,final),_,_=run([{"op":"finish"}],lambda g:(setattr(g,'kills',3),setattr(g,'finished',True)))
    blob=json.dumps(e,sort_keys=True)
    assert 'kill_count' not in blob and 'death_count' not in blob and 'independent-scorer' not in blob

if __name__=='__main__':
    tests=[(n,v) for n,v in globals().items() if n.startswith('test_')]
    for n,v in sorted(tests): v(); print('PASS',n)
