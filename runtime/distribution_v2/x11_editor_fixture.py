import json, os, pathlib, sys
from Xlib import X, XK, display
root=pathlib.Path(sys.argv[1]);connection=display.Display();screen=connection.screen()
window=screen.root.create_window(20,20,300,150,0,screen.root_depth,X.InputOutput,X.CopyFromParent,
    background_pixel=0x334455,event_mask=X.KeyPressMask|X.KeyReleaseMask)
window.map()
if len(sys.argv)>2 and sys.argv[2]=='textured':
    window.set_input_focus(X.RevertToParent,X.CurrentTime)
    screen.root.warp_pointer(68,68)
    gc=window.create_gc(foreground=0xffffff)
    for row in range(10):
        for col in range(18):
            if (row+col)%2==0:
                window.fill_rectangle(gc,col*16,row*16,16,16)
connection.sync()
(root/'app-ready.json').write_text(json.dumps({'window_id':window.id,'pid':os.getpid()}),encoding='utf-8')
text=''
with (root/'app-events.jsonl').open('x',encoding='utf-8',buffering=1) as log:
    while True:
        event=connection.next_event()
        if event.type not in (X.KeyPress,X.KeyRelease):continue
        key=connection.keycode_to_keysym(event.detail,0);name=XK.keysym_to_string(key)
        row={'type':'press' if event.type==X.KeyPress else 'release','keycode':event.detail,'keysym':name,'state':event.state}
        if event.type==X.KeyPress:
            if name=='s' and event.state & X.ControlMask:
                with (root/'saved.txt').open('x',encoding='utf-8') as output:
                    output.write(text);output.flush();os.fsync(output.fileno())
                row['effect']='saved'
            elif isinstance(name,str) and len(name)==1 and name.isascii() and name.isalpha() and not event.state & X.ControlMask:
                text+=name
                row['effect']='typed'
        log.write(json.dumps(row,sort_keys=True)+'\n')
