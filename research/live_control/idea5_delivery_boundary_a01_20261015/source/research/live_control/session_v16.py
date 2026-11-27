"""Candidate planner-declared local patch servo over the shared guided executor."""
import json
import numpy as np
from session_v15 import Backend as Previous,suite
from patch_servo import PatchServo
from executor_v3 import DecisionRequired

SERVO_SCHEMA={
    'op':'pointer_servo','program_constraint':'must be the only step',
    'required':{'source_sequence':'integer; latest observation sequence',
                'box':'[x,y,width,height] integers; size 4..96; spatial detail required',
                'target_delta':'[dx,dy] integers; each -32..32',
                'points':'2..32 objects {x: integer, y: integer}; within source frame',
                'duration_ms':'integer 1..5000; initial path only',
                'max_corrections':'integer 1..3'},
    'fixed':{'search_radius_px':32,'max_correction_px':24,'tolerance_px':1,
             'reply_timeout_ms':1000,'feedback_delay_ms':80},
    'outcomes':['local_goal_reached','lost','ambiguous','invalid_frame','same_observation','update_limit'],
    'completion':'non-goal outcome gives needs_decision; local goal is not independent task success'}

class Backend(Previous):
    def pixels(self):
        f=self.decoder.frame
        if f is None or f.mode!='RGB':raise ValueError('RGB source observation required')
        return np.frombuffer(f.pixels,dtype=np.uint8).reshape(f.height,f.width,3)
    def frame_identity(self):
        return json.dumps(self.observed_pointer,sort_keys=True)
    def guided(self,s):
        return dict(op='pointer_guided',points=s['points'],duration_ms=s['duration_ms'],
                    max_updates=s['max_corrections']+1,reply_timeout_ms=1000,feedback_delay_ms=80)
    def policy(self,s):
        if type(s['source_sequence'])is not int or s['source_sequence']!=self.sequence:raise ValueError('latest source_sequence required')
        return PatchServo(self.pixels(),s['box'],s['source_sequence'],self.frame_identity(),s['target_delta'],s['max_corrections'])
    def validate(self,steps):
        if not isinstance(steps,list) or not any(isinstance(s,dict) and s.get('op')=='pointer_servo' for s in steps):return super().validate(steps)
        if len(steps)!=1:raise ValueError('servo must be the only step')
        s=steps[0]
        if set(s)!={'op','source_sequence','box','target_delta','points','duration_ms','max_corrections'}:raise ValueError('invalid servo fields')
        if type(s['max_corrections'])is not int or not 1<=s['max_corrections']<=3:raise ValueError('max_corrections 1..3 required')
        self.policy(s);super().validate([self.guided(s)])
    def execute(self,s,cancel,identifier,index):
        if s['op']!='pointer_servo':return super().execute(s,cancel,identifier,index)
        policy=self.policy(s);emit=self.emit
        def local_emit(r):
            emit(r)
            if r.get('event')=='pointer_yield':
                state=self.owner.call('input_state')
                command=policy.reply(self.pixels(),r['sequence'],self.frame_identity(),state['pointer'])
                emit(dict(event='servo_feedback',id=identifier,step=index,**policy.records[-1]))
                self.reply_pointer(r['ticket'],r['sequence'],command)
        self.emit=local_emit
        try:super().execute(self.guided(s),cancel,identifier,index)
        finally:self.emit=emit
        reason=policy.records[-1]['reason'] if policy.records else 'no_feedback'
        emit(dict(event='servo_outcome',id=identifier,step=index,reason=reason,
                  local_goal_reached=reason=='local_goal_reached',semantic_effect_verified=False))
        if reason!='local_goal_reached':raise DecisionRequired()
