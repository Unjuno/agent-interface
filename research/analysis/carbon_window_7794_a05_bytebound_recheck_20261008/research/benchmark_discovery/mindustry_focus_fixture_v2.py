"""Test-only actual X11 focus fault after first acknowledged drag button-down."""
from Xlib import X,display
import mindustry_bend_interactive_v2 as entry
Previous=entry.Backend
class FaultBackend(Previous):
 def __init__(self,session,out,emit):
  self.controller=display.Display(session.name);self.sink=None;self.original=None;self.injected=False
  def wrapped(e):
   emit(e)
   if e['event']=='pointer_admission' and e.get('operation')=='button_down' and not self.injected:
    self.injected=True;self.original=self.controller.get_input_focus().focus
    self.sink=self.controller.screen().root.create_window(0,0,100,80,0,self.controller.screen().root_depth,override_redirect=True)
    self.sink.map();self.sink.set_input_focus(X.RevertToParent,X.CurrentTime);self.controller.sync()
    emit({'event':'fixture_focus_transferred','physical_button_down':bool(self.controller.screen().root.query_pointer().mask & X.Button1Mask)})
  super().__init__(session,out,wrapped)
 def snapshot(self,identifier,index):
  result=super().snapshot(identifier,index)
  if identifier=='observe-recovery' and self.original is not None:
   self.original.set_input_focus(X.RevertToParent,X.CurrentTime);self.controller.sync();self.original=None
   self.emit({'event':'fixture_focus_restored','scope':'test fixture restores focus after recovery snapshot; not agent refocus'})
  return result
 def close(self):
  try:super().close()
  finally:
   if self.original is not None:self.original.set_input_focus(X.RevertToParent,X.CurrentTime);self.controller.sync()
   if self.sink is not None:self.sink.destroy();self.controller.sync()
   self.controller.close()
entry.Backend=FaultBackend
if __name__=='__main__':entry.main()
