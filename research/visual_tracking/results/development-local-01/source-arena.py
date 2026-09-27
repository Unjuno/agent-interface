"""Private X11 moving-target fixture. State output is reserved for later scoring."""
import argparse,json,math,time
from pathlib import Path
from Xlib import X,XK,display


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--seconds',type=float,default=6);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();d=display.Display();screen=d.screen()
    w=screen.root.create_window(80,80,800,400,0,screen.root_depth,X.InputOutput,X.CopyFromParent,
        background_pixel=0x101010,event_mask=X.ExposureMask|X.KeyPressMask|X.KeyReleaseMask)
    w.set_wm_name('AI TRACK READY');w.map();d.flush()
    gc=w.create_gc();held=set();start=None;previous=time.perf_counter();player=400.;rows=[]
    phase=(a.seed%97)/97*2*math.pi
    def paint(t):
        target=400+250*math.sin(1.3*t+phase)
        gc.change(foreground=0x101010);w.fill_rectangle(gc,0,0,800,400)
        gc.change(foreground=0xffffff);w.draw_text(gc,20,30,b'Return starts. Track RED with GREEN using Left/Right.')
        gc.change(foreground=0xff2020);w.fill_rectangle(gc,round(target)-10,135,20,30)
        gc.change(foreground=0x20ff20);w.fill_rectangle(gc,round(player)-10,235,20,30)
        d.flush();return target
    while True:
        now=time.perf_counter()
        while d.pending_events():
            e=d.next_event()
            if e.type in (X.KeyPress,X.KeyRelease):
                key=d.keycode_to_keysym(e.detail,0)
                if e.type==X.KeyPress:
                    held.add(key)
                    if key==XK.XK_Return and start is None:start=now;previous=now;w.set_wm_name('AI TRACK RUNNING')
                else:held.discard(key)
        t=0 if start is None else now-start
        if start is not None:
            player=max(20,min(780,player+420*(now-previous)*((XK.XK_Right in held)-(XK.XK_Left in held))))
        target=paint(t)
        if start is not None:rows.append(dict(t=t,player=player,target=target,error=abs(player-target)))
        previous=now
        if start is not None and t>=a.seconds:
            a.out.write_text(json.dumps(rows));w.set_wm_name('AI TRACK DONE');d.flush()
            # Keep the final screen available until the session owner closes us.
            while True:time.sleep(1)
        time.sleep(.016)


if __name__=='__main__':main()
