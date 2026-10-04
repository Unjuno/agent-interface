"""Research-only one-shot appearance perturbation for assistant recovery.

This environment injector is not a production backend or controller feature.
"""
import time
from Xlib import X,display
from session_v21 import Backend as Candidate,suite,SERVO_SCHEMA

class Backend(Candidate):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.test_used=False;self.test_active=False;self.test_windows=[]
        self.test_display=display.Display(self.session.name)
    def snapshot(self,identifier,index):
        if self.test_active and not self.test_windows:
            parent=self.test_display.create_resource_object('window',self.observed_pointer['surface'])
            gx,gy=self.observed_pointer['geometry'][:2]
            for x,y,w,h,color in [(592,369,56,44,0xffffff),(620,373,48,36,0xff0000)]:
                win=parent.create_window(x-gx,y-gy,w,h,0,X.CopyFromParent,X.InputOutput,X.CopyFromParent,background_pixel=color,override_redirect=True)
                win.map();self.test_windows.append(win)
            self.test_display.sync();time.sleep(.04)
            self.emit(dict(event='environment_fixture',state='replacement_visible',scope='one-shot test perturbation; not controller input'))
        return super().snapshot(identifier,index)
    def execute(self,step,cancel,identifier,index):
        inject=step['op']=='pointer_servo' and not self.test_used
        if inject:self.test_used=True;self.test_active=True
        try:return super().execute(step,cancel,identifier,index)
        finally:
            if inject:
                self.test_active=False
                for win in self.test_windows:win.destroy()
                self.test_windows=[];self.test_display.sync()
                self.emit(dict(event='environment_fixture',state='replacement_removed',scope='environment restores after first servo; request fresh observation'))
    def close(self):
        try:super().close()
        finally:self.test_display.close()
