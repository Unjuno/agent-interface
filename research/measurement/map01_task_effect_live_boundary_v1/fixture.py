import argparse, json, os, sys, time, tkinter as tk

def append(path, obj):
    obj=dict(obj); obj.setdefault('t_ns', time.monotonic_ns())
    with open(path,'a',encoding='utf-8') as f:
        f.write(json.dumps(obj,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--schedule',required=True); ap.add_argument('--journal',required=True); ap.add_argument('--plan-id',required=True); ap.add_argument('--actuation-id',required=True); args=ap.parse_args()
    root=tk.Tk(); root.geometry('260x120+20+20'); root.title('task-effect-4131')
    label=tk.Label(root,text='fixture'); label.pack(); root.update_idletasks(); root.focus_force(); root.update()
    def event(kind, task_effect=False):
        append(args.journal, {'kind':kind,'schedule':args.schedule,'plan_id':args.plan_id,'actuation_id':args.actuation_id})
        if task_effect:
            append(args.journal, {'kind':'task_effect','source':kind,'scored':True,'plan_id':args.plan_id,'actuation_id':args.actuation_id})
    def on_press(e):
        event('key_press', args.schedule=='PRESS_EFFECT')
    def on_release(e):
        event('key_release', args.schedule=='RELEASE_EFFECT')
    root.bind_all('<KeyPress-a>', on_press); root.bind_all('<KeyRelease-a>', on_release)
    if args.schedule=='BACKGROUND_EFFECT':
        def bg(): append(args.journal, {'kind':'background_effect','source':'timer','scored':False,'plan_id':None,'actuation_id':None})
        root.after(220,bg)
    append(args.journal, {'kind':'ready','schedule':args.schedule,'plan_id':args.plan_id,'actuation_id':args.actuation_id})
    print(json.dumps({'ready':True,'window':root.winfo_id()}),flush=True)
    root.after(700, root.destroy)
    root.mainloop()
    append(args.journal, {'kind':'closed','schedule':args.schedule,'plan_id':args.plan_id,'actuation_id':args.actuation_id})
if __name__=='__main__': main()
