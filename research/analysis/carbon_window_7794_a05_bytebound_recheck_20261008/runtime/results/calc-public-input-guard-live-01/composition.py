"""Trusted app composition, same owner and guards on both routes."""
import copy,json,time
from pathlib import Path
from runtime.core_v1.compiled_gui import validate
from runtime.core_v1.contract import validate_program,SCHEMA_PROGRAM
from runtime.core_v1.sequence import expand_text_gaps
from runtime.guarded_x11_v1.compiled import surface
from observation_cue import CalcObservationCue,bridge_context
from save_guard import SemanticSaveGuard

class Stop(Exception):
    def __init__(self,reason):self.reason=reason

def plans(bridge,refs,second_value):
    entry=[{'op':'text','text':'731','gap_ms':1},{'op':'key_chord','keys':['Return']},{'op':'wait_update','timeout_ms':100},
           {'op':'text','text':second_value,'gap_ms':1},{'op':'key_chord','keys':['Return']},{'op':'wait_update','timeout_ms':100}]
    save=[{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':100}]
    bindings={'enter':{'interaction':'click','offset':refs['entry_offset'],'tail':entry},
              'save':{'interaction':'keyboard','offset':refs['save_offset'],'tail':save}}
    symbols={name:{'kind':'target_reference','target_reference':refs[name+'_alias'],'identity_predicate':'context_ok','dependencies':['context_ok']} for name in ['entry','save']}
    symbols['save']['dependencies'].append('cells_filled')
    def branch(when,action,next_state):return {'when':when,'outcome':'action','action':action,'next_state':next_state,'reason':None}
    interface={'format':'compiled-gui-interface-v1','interface_id':'calc-entry-checked-save','session_scope':bridge.scope,'surface':surface(bridge),
     'predicates':['context_ok','blank','cells_filled'],'symbols':symbols,
     'actions':{'enter':{'target_symbol':'entry','operation':'enter_pair','expected_effect':{'cells_filled':True}},
                'save':{'target_symbol':'save','operation':'request_xlsx_save','expected_effect':{'cells_filled':True}}},
     'method':{'name':'enter-check-request-save','version':'1','initial_state':'initial','max_transitions':2,'max_runtime_ms':5000,
      'states':{'initial':{'branches':[branch({'context_ok':True,'blank':True},'enter','filled')]},
                'filled':{'branches':[branch({'context_ok':True,'cells_filled':True},'save','handoff')]},
                'handoff':{'branches':[{'when':{'context_ok':True},'outcome':'yield','action':None,'next_state':None,'reason':'effect_unavailable'}]}}}}
    interface=validate(interface)
    # Validate the actual expanded entry/Save op schemas before allocation/input.
    for action,b in bindings.items():
        tail=expand_text_gaps(b['tail'],max_ops=123 if action=='enter' else 126)[0]
        pointer=[] if action=='save' else [{'op':'pointer_move','frame':'screen_physical_px','x':10,'y':10},{'op':'pointer_button','button':'left','down':True},{'op':'pointer_button','button':'left','down':False}]
        validate_program({'schema':SCHEMA_PROGRAM,'program_id':'calc-preflight-'+action,'source':{'observation_seq':1,'binding_revision':0},
          'authority':{'lease_id':'calc-preflight','expires_at_ns':1},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'app'},*pointer,*tail,{'op':'release_all'}]})
    return interface,bindings

class CalcComposition:
    def __init__(self,owner,root,*,refs,approved,reviewed_native,reviewed_rgb,second_value='864',clock=time.monotonic_ns,ocr_runner=None):
        self.owner=owner;self.bridge=owner.bridge;self.root=Path(root);self.root.mkdir(parents=True,exist_ok=False)
        self.refs=copy.deepcopy(refs);self.clock=clock;self.deadline=clock()+5_000_000_000
        b=self.bridge
        if reviewed_native['sequence']!=b.sequence or b.history[b.sequence][0]!=reviewed_native or b.history[b.sequence][1].tobytes()!=reviewed_rgb.tobytes():
            raise ValueError('exact fresh primary-reviewed blank source required')
        self.blank_pixels=[reviewed_rgb.crop(box).tobytes() for box in refs['cell_regions']]
        self.context_pixels=reviewed_rgb.crop(refs['context_region']).tobytes()
        self.interface,self.bindings=plans(b,refs,second_value)
        kwargs={} if ocr_runner is None else {'runner':ocr_runner}
        self.cue=CalcObservationCue(capture_root=self.root,evidence_root=self.root/'ocr',approved=approved,context=lambda:bridge_context(b),deadline_ns=self.deadline,clock=clock,**kwargs)
        self.guard=SemanticSaveGuard(owner,alias=refs['save_alias'],offset=refs['save_offset'],regions=refs['cell_regions'],deadline_ns=self.deadline,clock=clock)
        self.trace=[]
        (self.root/'plan.json').write_text(json.dumps({'interface':self.interface,'bindings':self.bindings,'refs':refs,'primary_blank_review_sequence':reviewed_native['sequence'],'save_is_request_not_persistence':True},indent=2)+'\n')

    def perceive(self,native,rgb):
        result=self.cue(native,rgb)
        context=result['source_context_verified'] and rgb.crop(self.refs['context_region']).tobytes()==self.context_pixels
        blank=context and all(rgb.crop(box).tobytes()==pixels for box,pixels in zip(self.refs['cell_regions'],self.blank_pixels))
        filled=context and result['cells']=='filled'
        if filled and self.guard.snapshot is None:
            record=json.loads((self.root/'ocr'/f'{self.cue.calls:03d}.json').read_text())
            self.guard.arm(native,rgb,cue_record=record)
        values={'context_ok':bool(context),'blank':bool(blank),'cells_filled':True if filled else (False if result['cells']=='wrong' else 'unknown')}
        self.trace.append({'sequence':native['sequence'],'predicates':copy.deepcopy(values),'known_ns':self.clock()})
        return values

    def verify(self,payload,native,rgb):
        return {'status':'succeeded' if payload['action']=='enter' else 'unavailable','evidence_ref':payload['observation']['evidence_ref']}

    def run(self,route):
        b=self.bridge;original_keyboard=b.keyboard
        try:
            with self.guard.install_for_save(self.bindings['save']['tail']):
                if route=='compiled':
                    result=self.owner.run_compiled(self.interface,self.bindings,call_root=self.root/'call',perceive=self.perceive,verify_effect=self.verify)
                elif route=='ordinary':result=self.ordinary()
                else:raise ValueError('unknown route')
            (self.root/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
        finally:
            if b.keyboard!=original_keyboard:raise RuntimeError('temporary Save wrapper not restored')
            (self.root/'trace.json').write_text(json.dumps(self.trace,indent=2)+'\n')
            (self.root/'guard-events.json').write_text(json.dumps(self.guard.events,indent=2)+'\n')

    def ordinary(self):
        b=self.bridge;self.owner.dispatch_attempted=True
        b.backend.configure_capture_artifacts(self.root/'call/images',retain_rgb=True)
        count=0;observations=[];pending=None
        def observe():
            if self.clock()>=self.deadline:raise Stop('budget_exhausted')
            native=b.observe();p=self.perceive(native,b.history[native['sequence']][1])
            observations.append({'sequence':native['sequence'],'predicates':p});return native,p
        try:
            native,p=observe()
            if p['context_ok'] is not True or p['blank'] is not True:raise Stop('unknown_state')
            for action in ['enter','save']:
                if self.clock()>=self.deadline:raise Stop('budget_exhausted')
                if action=='save' and p['cells_filled'] is not True:raise Stop('effect_unavailable')
                name='entry' if action=='enter' else 'save';args=self.bindings[action];rgb=b.history[native['sequence']][1]
                resolution=b.store.resolve_point(self.refs[name+'_alias'],args['offset'],native,rgb,self.clock(),session_scope=self.interface['session_scope'])
                if not resolution['eligible']:raise Stop('authority_unavailable')
                previous_digest=native['native']['artifact']['sha256']
                result=(b.click if action=='enter' else b.keyboard)(self.refs[name+'_alias'],args['offset'],tail=copy.deepcopy(args['tail']),expires_at_ns=min(self.deadline,resolution['valid_until_ns']))
                releases=result.get('execution',{}).get('releases',[])
                if not releases or not all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in releases):raise Stop('execution_failed')
                if result.get('status')!='completed' or b.session.recovery_required:raise Stop('execution_failed')
                count+=1;pending=action;native,p=observe()
                if native['native']['artifact']['sha256']==previous_digest:raise Stop('no_progress')
                if p['cells_filled'] is not True:raise Stop('effect_unavailable' if p['cells_filled']=='unknown' else 'effect_failed')
                if action=='save':raise Stop('effect_unavailable')
                pending=None
        except Stop as error:reason=error.reason
        except Exception as error:
            from runtime.core_v1.compiled_gui import ObservationAssociationChanged
            if not isinstance(error,ObservationAssociationChanged):raise
            reason='association_changed'
        feedback=None
        if observations:
            try:
                sequence=observations[-1]['sequence']
                if sequence!=b.sequence or b.review_required:
                    raise ValueError('final ordinary observation no longer matches this owner')
                source,_=b.history[sequence]
                from runtime.cli_v1.review import present_result
                feedback=present_result({'schema':'agent-interface/runtime-observation-v1','status':'returned','observation_id':source['observation_id'],
                    'observation':source['native'],'input_dispatched':False,'side_effect_authority':False},self.root/'call',compact=True,report_refs=True)
                if feedback.get('image_status')!='image':b.review_required=True
            except Exception as error:
                b.review_required=True
                feedback={'image_status':'needs_review','image':None,'error':repr(error),'replay_allowed':False}
        return {'feedback':feedback,'method_receipt':{'outcome':'SAFE_YIELD','reason':reason,'completed_transitions':count,'pending_effect':pending,'observations':observations},'task_success':None,'replay_allowed':False}
