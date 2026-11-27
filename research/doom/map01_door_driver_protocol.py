"""Deterministic, zero-model command protocol for the finite door trial.

This is not an evidence verifier: it sends the fixed commands only after the
runtime's own settlement gate reports DONE. Private scorer data is never read.
"""
from map01_reverse_program import reverse_stages, reverse_manifest

class DoorDriverProtocol:
    def __init__(self, arm, manifest_sha, save_sha, evidence_sha, restore_tic, *, traverse=False, exit_probe=False, exit_arm=None, direct_exit=False, reverse_arm=None):
        if arm not in ('control','use') or type(restore_tic) is not int:
            raise ValueError('invalid registered trial')
        if type(traverse) is not bool:raise ValueError('invalid traversal mode')
        if (type(exit_probe) is not bool or exit_probe and (not traverse or exit_arm not in ('control','use'))
                or not exit_probe and exit_arm is not None):raise ValueError('invalid exit probe mode')
        if type(direct_exit) is not bool or direct_exit and not exit_probe:raise ValueError('invalid direct exit mode')
        if reverse_arm is not None and (reverse_arm not in ('control','use','calibrate','east-return','east-return-turn75','east-return-reopen') or not traverse or arm!='use' or exit_probe or direct_exit):
            raise ValueError('reverse mode requires the use/traverse prefix without exit probe')
        self.reverse_arm=reverse_arm
        self.direct_exit=direct_exit
        self.arm=arm
        self.traverse=traverse
        self.exit_probe=exit_probe
        self.exit_arm=exit_arm
        self.manifest_sha=manifest_sha
        self.save_sha=save_sha
        self.evidence_sha=evidence_sha
        self.restore_tic=restore_tic
        self.ready=False
        self.pending=None
        self.typed=None
        self.latest=None
        self.identity=None
        self.index=0
        self.stage='ready'
        self.settling=False

    def _submit(self, identifier, steps, now):
        if (self.latest is None or self.typed is not None or type(now) is not int
                or not 0<=now-self.latest['capture_ns']<2_000_000_000):
            raise ValueError('fresh completed observation required')
        self.pending=identifier
        return {'op':'submit','id':identifier,'steps':steps,
                'expected_sequence':self.latest['sequence'],'valid_until_ns':now+20_000_000_000}

    def receive(self, row, now):
        if type(row) is not dict or type(row.get('event')) is not str or type(now) is not int:
            raise ValueError('invalid runtime event')
        event=row['event']
        if event in ('rejected','pointer_admission','input_release_unverified'):
            raise ValueError('runtime rejected trial or input became unverified')
        if event=='ready':
            fixture=row.get('fixture')
            proof=fixture.get('setup_candidate_evidence') if type(fixture) is dict else None
            if (self.reverse_arm is None and 'reverse_door_program' in row
                    or self.reverse_arm is not None and row.get('reverse_door_program')!=reverse_manifest(self.reverse_arm)):
                raise ValueError('reverse program binding differs')
            if (self.ready or type(proof) is not dict or fixture.get('manifest_sha256')!=self.manifest_sha
                    or fixture.get('save_sha256')!=self.save_sha or fixture.get('after_load_tic')!=self.restore_tic
                    or proof.get('evidence_sha256')!=self.evidence_sha
                    or row.get('post_load_clock_gate',{}).get('passed') is not True):
                raise ValueError('ready candidate binding differs')
            self.ready=True
            return None
        if event=='typed_observation':
            expected=self.pending if self.pending else ('initial' if self.index==0 else None)
            seq=row.get('sequence');capture=row.get('capture_ns');binding=row.get('pointer_binding')
            process=row.get('target_process_identity');window=row.get('target_renewal_window_identity')
            if (not self.ready or self.typed is not None or row.get('id')!=expected
                    or type(seq) is not int or seq<1 or type(capture) is not int
                    or not 0<=now-capture<2_000_000_000 or type(binding) is not dict
                    or type(binding.get('surface')) is not int or binding.get('focus')!=binding['surface']
                    or type(process) is not dict or process.get('sequence')!=seq or process.get('surface')!=binding['surface']
                    or type(window) is not dict or window.get('sequence')!=seq or window.get('surface')!=binding['surface']
                    or type(process.get('digest')) is not str or type(window.get('digest')) is not str
                    or type(row.get('renewal_owner_id')) is not str or not row['renewal_owner_id']
                    or type(row.get('input_owner_generation')) is not int
                    or type(row.get('frame_rgb_sha256')) is not str or len(row['frame_rgb_sha256'])!=64):
                raise ValueError('typed observation differs')
            identity=(binding['surface'],row['renewal_owner_id'],row['input_owner_generation'],process['digest'],window['digest'])
            if self.identity is not None and identity!=self.identity:
                raise ValueError('target changed')
            if self.latest is not None and seq<=self.latest['sequence']:
                raise ValueError('observation sequence did not advance')
            signals=row.get('signals')
            if type(signals) is not dict:
                raise ValueError('HUD signals missing')
            for name,value in (('health',100),('ammo',50)):
                item=signals.get(name)
                known=(type(item) is dict and item.get('status')=='observed' and type(item.get('value')) is int and item['value']==value)
                terminal_unknown=(self.exit_probe and self.pending=='exit-probe' and type(item) is dict
                                  and item.get('status')=='unknown' and item.get('value') is None)
                if (not (known or terminal_unknown) or item.get('sequence')!=seq or item.get('capture_ns')!=capture
                        or item.get('binding')!=binding or item.get('signal_id')!=name):
                    raise ValueError('HUD signal differs')
            self.identity=identity
            self.typed=row
            return None
        if event=='observation':
            early=self.typed
            fields=('id','step','sequence','capture_ns','frame_rgb_sha256','pointer_binding',
                    'renewal_owner_id','input_owner_generation','target_process_identity','target_renewal_window_identity')
            if (early is None or any(early.get(k)!=row.get(k) for k in fields)
                    or row.get('exact') is not True or row.get('focus_samples_match') is not True
                    or row.get('input_focus_before')!=row['pointer_binding']['focus']
                    or row.get('input_focus_after')!=row['pointer_binding']['focus']):
                raise ValueError('full observation differs from typed observation')
            self.latest=row
            self.typed=None
            if self.pending is None and self.index==0:
                self.stage='running'
                return self._submit('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}],now)
            return None
        if event=='terminal':
            if self.pending is None or row.get('id')!=self.pending or row.get('status')!='completed' or self.typed is not None:
                raise ValueError('unexpected or incomplete terminal')
            self.settling=True
            return {'op':'door-settle'}
        if event=='door_settle':
            if not self.settling or row.get('operation_id')!=self.pending:
                raise ValueError('unexpected settlement')
            if row.get('status')=='WAIT':
                return {'op':'door-settle'}
            if row.get('status')!='DONE' or self.latest is None or self.latest.get('id')!=self.pending:
                raise ValueError('operation did not settle with observation')
            self.index+=1
            self.pending=None
            self.settling=False
            if self.direct_exit and self.index==1:
                steps=([{'op':'hold','keys':['e'],'duration_ms':120}] if self.exit_arm=='use'
                       else [{'op':'coast','duration_ms':120,'sample_ms':100}])
                return self._submit('exit-probe',steps,now)
            if self.direct_exit and self.index==2:
                self.stage='finish'
                return {'op':'finish'}
            if self.index<=4:
                return self._submit('approach-'+str(self.index),[{'op':'hold','keys':['Up'],'duration_ms':600}],now)
            if self.index==5:
                steps=([{'op':'hold','keys':['e'],'duration_ms':120}] if self.arm=='use'
                       else [{'op':'coast','duration_ms':120,'sample_ms':100}])
                return self._submit('intervention',steps,now)
            if self.index==6 and self.traverse:
                return self._submit('traverse-1',[{'op':'hold','keys':['Up'],'duration_ms':300 if self.reverse_arm is not None else 600}],now)
            if self.reverse_arm is not None and self.index>=7:
                stages=reverse_stages(self.reverse_arm)
                offset=self.index-7
                if offset<len(stages):
                    identifier,steps=stages[offset]
                    return self._submit(identifier,steps,now)
                if offset==len(stages):
                    self.stage='finish'
                    return {'op':'finish'}
                raise ValueError('too many reverse operations')
            if self.index==7 and self.exit_probe:
                steps=([{'op':'hold','keys':['e'],'duration_ms':120}] if self.exit_arm=='use'
                       else [{'op':'coast','duration_ms':120,'sample_ms':100}])
                return self._submit('exit-probe',steps,now)
            if self.index==(8 if self.exit_probe else 7 if self.traverse else 6):
                self.stage='finish'
                return {'op':'finish'}
            raise ValueError('too many operations')
        return None
