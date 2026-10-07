"""Research-only segmented drag with observations while the button is held.

Not a claim that pixels acknowledge button consumption. Each segment offers
feedback and lets application rendering progress. The public final movement
predicate remains mandatory; no retry is silently converted to success.
"""
import time
import gui_suite as suite

original_controller=suite.controller


def controller(session,app,goal,observer):
    if app!="inkscape": return original_controller(session,app,goal,observer)
    driver=suite.base.Driver(session,0)
    observer.sample("initial","initial")
    observer.action("selection_tool",lambda:driver.key("F1"),lambda f,c:suite.red_bbox(f) is not None)
    observer.action("select_all",lambda:driver.chord("Control_L","a"),lambda f,c:suite.selection_visible(f))
    box=suite.red_bbox(observer.last); x=(box[0]+box[2])//2; y=(box[1]+box[3])//2
    before=box[0]
    events=[]
    def event(kind,**args):
        issued=time.perf_counter_ns()
        suite.base.xtest.fake_input(session.d,kind,**args); session.d.sync()
        events.append(dict(kind=kind,arguments=args,issued_ns=issued,ack_ns=time.perf_counter_ns()))
        driver.input_events+=1
    def drag():
        event(suite.base.X.MotionNotify,x=x,y=y)
        event(suite.base.X.ButtonPress,detail=1)
        try:
            # Retain A1's tested input dwell, and expose a frame before motion.
            time.sleep(.030)
            observer.sample("drag_right","button_held_feedback")
            steps=max(4,min(12,int(goal["dx"]//4)))
            for i in range(1,steps+1):
                event(suite.base.X.MotionNotify,x=round(x+goal["dx"]*i/steps),y=y)
                observer.sample("drag_right","motor_segment_feedback")
        finally:
            event(suite.base.X.ButtonRelease,detail=1)
        driver.pointer_path+=goal["dx"]; driver.logical_ops+=1
    def moved(frame,context):
        current=suite.red_bbox(frame)
        return current is not None and current[0]>=before+2
    observer.action("drag_right",drag,moved)
    action=observer.actions[-1]
    first=next(s["ready_ns"] for s in observer.samples if s["update"].action_id=="drag_right")
    action["first_feedback_ns"]=first
    action["first_feedback_ms"]=(first-action["issued_ns"])/1e6
    # input_ack remains full gesture injection completion; first feedback can
    # precede it. Individual X11 event acknowledgments are recorded separately.
    observer.action("save",lambda:driver.chord("Control_L","s"))
    return dict(logical_ops=driver.logical_ops,input_events=driver.input_events,
                pointer_path_px=driver.pointer_path,motor_events=events)
