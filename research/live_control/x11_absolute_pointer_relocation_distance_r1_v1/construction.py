from common import *

def main():
    p,name=start_xvfb(); rows=[]
    try:
        actor=display.Display(name); observer=display.Display(name)
        for d in DISTANCES:
            reset(actor,observer); t0,t1=move_sync(actor,CX+d,CY); x,y,mask=read_pointer(observer)
            rows.append({'distance':d,'duration_ns':t1-t0,'exact':(x,y)==(CX+d,CY),'neutral':(mask&BUTTON_MASK)==0})
        reset(actor,observer); near=stepwise(actor,8); x,y,mask=read_pointer(observer); assert (x,y)==(CX+8,CY)
        reset(actor,observer); far=stepwise(actor,256); x,y,mask=read_pointer(observer); assert (x,y)==(CX+256,CY)
        checks={'absolute_exact':all(r['exact'] for r in rows),'neutral':all(r['neutral'] for r in rows),'stepwise_sensitivity':far>near,'positive_durations':all(r['duration_ns']>0 for r in rows)}
        print({'display':name,'rows':rows,'stepwise_near_ns':near,'stepwise_far_ns':far,'checks':checks})
        assert all(checks.values())
        actor.close();observer.close()
    finally: stop_xvfb(p)
if __name__=='__main__':main()
