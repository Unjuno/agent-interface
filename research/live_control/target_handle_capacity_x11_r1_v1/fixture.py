import argparse,json,os,tkinter as tk
from patterns import SIZE,rgb_for

p=argparse.ArgumentParser();p.add_argument('--title');p.add_argument('--log');p.add_argument('--command');a=p.parse_args()
root=tk.Tk(); root.withdraw()
generation=0; surface=None; canvas=None; images=[]

def log(obj):
    with open(a.log,'a',encoding='utf-8') as f:
        f.write(json.dumps(obj,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())

def mkimage(label):
    im=tk.PhotoImage(width=SIZE,height=SIZE)
    rows=[]
    for y in range(SIZE):
        row=[]
        for x in range(SIZE):
            r,g,b=rgb_for(label,x,y); row.append(f'#{r:02x}{g:02x}{b:02x}')
        rows.append('{'+ ' '.join(row) +'}')
    im.put(' '.join(rows)); return im

def build():
    global surface,canvas,images
    surface=tk.Toplevel(root); surface.title(a.title); surface.geometry('400x240+40+40'); surface.resizable(False,False)
    canvas=tk.Canvas(surface,width=400,height=240,bg='#202830',highlightthickness=0); canvas.pack(fill='both',expand=True)
    images=[mkimage('A'),mkimage('B')]
    # exact top-left locations in client coordinates
    loc={'A':(80,100),'B':(280,100)}
    for lab,im in zip(('A','B'),images):
        x,y=loc[lab];canvas.create_image(x,y,image=im,anchor='nw')
    def click(ev):
        hit='WRONG'
        for lab,(x,y) in loc.items():
            if x<=ev.x<x+SIZE and y<=ev.y<y+SIZE:hit=lab
        log({'event':'click','generation':generation,'target':hit,'x':ev.x,'y':ev.y})
    canvas.bind('<Button-1>',click)
    surface.update_idletasks();surface.update()
    xid=surface.winfo_id();log({'event':'surface','generation':generation,'surface_xid':xid})
    try: surface.focus_force()
    except Exception: pass

def check():
    global generation,surface
    try:
        cmd=open(a.command,encoding='utf-8').read().strip() if os.path.exists(a.command) else ''
    except Exception:cmd=''
    if cmd=='replace':
        open(a.command,'w').close()
        if surface is not None: surface.destroy()
        generation+=1; build()
    root.after(10,check)

build();root.after(10,check);root.mainloop()
