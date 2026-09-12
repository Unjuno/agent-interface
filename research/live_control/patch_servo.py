"""Bounded deterministic reply policy; shared backend retains all input authority."""
from visual_anchor import VisualAnchor

class PatchServo:
    def __init__(self,image,box,observation_id,frame_id,target_delta,max_updates=3,max_step=24):
        if len(target_delta)!=2 or any(type(v)is not int or abs(v)>32 for v in target_delta):raise ValueError('bounded integer target required')
        if type(max_updates)is not int or not 1<=max_updates<=4:raise ValueError('updates 1..4 required')
        if type(max_step)is not int or not 1<=max_step<=24:raise ValueError('step 1..24 required')
        self.anchor=VisualAnchor(image,box,observation_id,frame_id)
        self.target=tuple(target_delta);self.remaining=max_updates;self.max_step=max_step
        self.records=[];self.done=False

    def reply(self,image,observation_id,frame_id,pointer):
        if self.done:raise ValueError('servo already terminal')
        result=self.anchor.locate(image,observation_id,frame_id)
        if result['status']!='matched':reason=result['status'];command={'op':'finish'}
        else:
            error=[t-d for t,d in zip(self.target,result['delta'])]
            if max(map(abs,error))<=1:reason='local_goal_reached';command={'op':'finish'}
            elif self.remaining==0:reason='update_limit';command={'op':'finish'}
            else:
                reason='correct';self.remaining-=1
                delta=[max(-self.max_step,min(self.max_step,v)) for v in error]
                command={'op':'move','x':pointer[0]+delta[0],'y':pointer[1]+delta[1]}
        self.done=command['op']=='finish'
        self.records.append({'observation':observation_id,'tracking':result,'reason':reason,'command':command,'updates_remaining':self.remaining})
        return command
