import json,pathlib,time
from Xlib import X,display
O=pathlib.Path('/out');d=display.Display(':161');s=d.screen();w=s.root.create_window(0,0,640,360,0,s.root_depth,X.InputOutput,X.CopyFromParent,background_pixel=0xffffff,event_mask=X.ExposureMask|X.ButtonPressMask|X.ButtonReleaseMask)
w.set_wm_name('owned schema assay');w.map();d.sync();font=d.open_font('fixed');gc=w.create_gc(foreground=0,font=font.id);press=None;history=[];selected=None
def write(name,obj):
 p=O/(name+'.tmp');p.write_text(json.dumps(obj));p.replace(O/(name+'.json'))
def draw():
 w.clear_area();w.draw_text(gc,40,60,'Choose exactly one labelled button')
 for x,label,color in [(60,'GREEN',0x90ee90),(350,'BLUE',0x87cefa)]:
  g=w.create_gc(foreground=color);w.fill_rectangle(g,x,140,220,90);g.free();w.rectangle(gc,x,140,220,90);w.draw_text(gc,x+80,190,label)
 if selected:
  g=w.create_gc(foreground=0x90ee90 if selected=='GREEN' else 0x87cefa);w.fill_rectangle(g,60,280,220,40);g.free();w.draw_text(gc,70,305,'Selected: '+selected)
 d.sync()
draw();write('fixture-ready',dict(window=w.id,width=640,height=360));write('effect',dict(history=[],press=None))
while True:
 e=d.next_event()
 if e.type==X.Expose:draw()
 elif e.type==X.ButtonPress:
  press=dict(x=e.event_x,y=e.event_y,button=e.detail,time=e.time);write('effect',dict(history=history,press=press))
 elif e.type==X.ButtonRelease:
  label='GREEN' if 60<=e.event_x<280 and 140<=e.event_y<230 else 'BLUE' if 350<=e.event_x<570 and 140<=e.event_y<230 else 'NONE'
  history.append(dict(label=label,x=e.event_x,y=e.event_y,button=e.detail,time=e.time,matching_press=press is not None and press['button']==e.detail));press=None;selected=label;draw();write('effect',dict(history=history,press=press,selected=selected))
