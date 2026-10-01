"""Collect development-known, static widget pixels on a newly owned Xvfb."""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path


def collect(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    r, w = os.pipe()
    command = ['Xvfb', '-displayfd', str(w), '-screen', '0', '1024x768x24', '-nolisten', 'tcp']
    err = (out / 'xvfb.stderr').open('wb')
    server = subprocess.Popen(command, pass_fds=(w,), stdout=subprocess.DEVNULL, stderr=err)
    os.close(w)
    receipt = {'command': command, 'pid': server.pid, 'start_ns': time.monotonic_ns(), 'captures': []}
    root = display = None
    number = None
    try:
        if not select.select([r], [], [], 5)[0]:
            raise TimeoutError('Xvfb display acquisition')
        number = int(os.read(r, 32).strip())
        os.environ['DISPLAY'] = ':' + str(number)
        os.environ['XAUTHORITY'] = '/dev/null'
        import tkinter as tk
        from tkinter import ttk
        from Xlib import X, display as xd
        from PIL import Image
        root = tk.Tk()
        root.overrideredirect(True)
        root.geometry('800x480+0+0')
        display = xd.Display(os.environ['DISPLAY'])
        screen = display.screen()
        visual = next(v for depth in screen.allowed_depths for v in depth.visuals if v.visual_id == screen.root_visual)
        formats = [f._data for f in display.display.info.pixmap_formats]
        receipt.update(display=os.environ['DISPLAY'], tk=root.tk.call('info', 'patchlevel'),
                       byte_order=display.display.info.image_byte_order, formats=formats,
                       depth=screen.root_depth, masks=[visual.red_mask, visual.green_mask, visual.blue_mask])
        if receipt['byte_order'] != X.LSBFirst or screen.root_depth != 24 or receipt['masks'] != [16711680,65280,255]:
            raise RuntimeError('unsupported captured pixel layout')
        if not any(f['depth']==24 and f['bits_per_pixel']==32 and f['scanline_pad']==32 for f in formats):
            raise RuntimeError('unsupported stride')
        for scene in ('form', 'table', 'canvas'):
            for child in root.winfo_children(): child.destroy()
            if scene == 'form':
                ttk.Label(root, text='Research workspace - observation fixture', font=('DejaVu Sans', 18)).pack(pady=14)
                for i, label in enumerate(('Project', 'Source', 'Revision', 'Output', 'Status', 'Owner')):
                    row = ttk.Frame(root); row.pack(fill='x', padx=30, pady=9)
                    ttk.Label(row, text=label, width=16).pack(side='left')
                    entry = ttk.Entry(row, width=60); entry.pack(side='left', fill='x', expand=True)
                    entry.insert(0, f'{label.lower()}-{i:03d}-static-development-fixture')
                ttk.Button(root, text='Save (no input is sent)').pack(pady=12)
            elif scene == 'table':
                columns = ('id','name','state','count','latency')
                tree = ttk.Treeview(root, columns=columns, show='headings', height=22)
                for name in columns:
                    tree.heading(name,text=name.upper()); tree.column(name,width=150)
                for i in range(30):
                    tree.insert('', 'end', values=(f'R{i:03d}', f'static-item-{i:02d}', ['READY','PENDING','DONE'][i%3], i*17, f'{i*7+13}.00 ms'))
                tree.pack(fill='both',expand=True)
            else:
                c = tk.Canvas(root, width=800,height=480,bg='white',highlightthickness=0); c.pack()
                for x in range(0,800,20): c.create_line(x,0,x,480,fill='#dddddd')
                for y in range(0,480,20): c.create_line(0,y,800,y,fill='#dddddd')
                for i in range(20):
                    x=25+(i%5)*155; y=25+(i//5)*115
                    c.create_rectangle(x,y,x+120,y+75,fill=['#dbeeff','#ffe6cd','#d9f2da'][i%3],outline='#333333',width=2)
                    c.create_text(x+60,y+24,text=f'Node {i:02d}',font=('DejaVu Sans',13))
                    c.create_text(x+60,y+49,text=f'value = {i*31}',font=('DejaVu Sans',10))
            root.update_idletasks(); root.update(); display.sync()
            begin=time.monotonic_ns()
            image=screen.root.get_image(0,0,800,480,X.ZPixmap,0xffffffff)
            end=time.monotonic_ns()
            raw=bytes(image.data)
            if len(raw)!=800*480*4: raise RuntimeError('capture length')
            rgb=Image.frombytes('RGB',(800,480),raw,'raw','BGRX').tobytes()
            (out/(scene+'.bgrx')).write_bytes(raw)
            (out/(scene+'.rgb')).write_bytes(rgb)
            receipt['captures'].append({'scene':scene,'width':800,'height':480,'start_ns':begin,'end_ns':end,
                 'bgrx_sha256':hashlib.sha256(raw).hexdigest(),'rgb_sha256':hashlib.sha256(rgb).hexdigest()})
    except BaseException as exc:
        receipt['error']=repr(exc)
        raise
    finally:
        if display is not None: display.close()
        if root is not None: root.destroy()
        server.terminate()
        try: receipt['server_exit']=server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill(); receipt['server_exit']=server.wait(); receipt['forced_cleanup']=True
        os.close(r); err.close()
        receipt['socket_absent']=number is not None and not Path('/tmp/.X11-unix/X'+str(number)).exists()
        receipt['end_ns']=time.monotonic_ns()
        (out/'CAPTURE.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')

if __name__=='__main__': collect(sys.argv[1])
