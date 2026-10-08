"""Test-only real X11 target/focus mutation during the model wait interval."""
import os,threading,time
from Xlib import X,display
import mindustry_bend_interactive_v2 as entry
Previous=entry.Backend
class MutatingBackend(Previous):
 def __init__(self,session,out,emit):
  super().__init__(session,out,emit);self.display_name=session.name;self.controller=display.Display(session.name);self.worker=None;self.changed=threading.Event();self.restore=threading.Event()
 def mutate(self):
  time.sleep(1)
  d=self.controller;original=d.get_input_focus().focus;kind=os.environ['AI_STUDY_MUTATION']
  x,y,w,h=(985,551,47,52) if kind=='patch' else (0,0,100,80)
  window=d.screen().root.create_window(x,y,w,h,0,d.screen().root_depth,override_redirect=True,background_pixel=0xff0000)
  try:
   window.map()
   if kind=='focus':window.set_input_focus(X.RevertToParent,X.CurrentTime)
   d.sync();self.emit({'event':'fixture_mutation','kind':kind,'fixture_window':window.id,'original_focus':original.id,'at_ns':time.perf_counter_ns()});self.changed.set()
   self.restore.wait(90)
  finally:
   if kind=='focus':original.set_input_focus(X.RevertToParent,X.CurrentTime)
   window.destroy();d.sync();self.emit({'event':'fixture_restored','kind':kind,'at_ns':time.perf_counter_ns()});d.close()
 def snapshot(self,identifier,index):
  if identifier=='intent-revalidation' and not self.changed.wait(5):raise RuntimeError('fixture mutation missing')
  result=super().snapshot(identifier,index)
  if identifier=='model-observation' and self.worker is None:
   self.worker=threading.Thread(target=self.mutate);self.worker.start()
  if identifier=='intent-revalidation':self.restore.set();self.worker.join(5)
  return result
 def close(self):
  self.restore.set()
  if self.worker:self.worker.join(5)
  super().close()
entry.Backend=MutatingBackend
if __name__=='__main__':entry.main()
