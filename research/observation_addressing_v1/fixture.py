"""Network-free staged fixture; app event handler emits scorer-only receipts."""
import json

CASES=('stable_small','linear_move','unexpected_jump','duplicate_visual',
       'duplicate_native','canvas_only','semantic_conflict','occluded','removed','identity_swap')

def html(case, layout, phase, token):
    # Fixture driver owns these constants. They never enter resolver inputs.
    x,y=211+128*layout,173+64*layout
    moving=case in ('linear_move','unexpected_jump')
    if moving: x += (phase-1)*32
    if phase==2 and case=='unexpected_jump': x+=160
    if phase==2 and case=='identity_swap': x+=180
    canvas=case=='canvas_only'
    name='Cancel' if phase==2 and case=='semantic_conflict' else 'Save'
    boxes=[]
    def button(x,y,color,name,which):
        return (f'<button aria-label="{name}" style="left:{x}px;top:{y}px;background:{color}" '
                f'onclick="send(event,\'{which}\')"></button>')
    if not (phase==2 and case=='removed'):
        if canvas:
            boxes.append(f'<canvas width="22" height="16" style="left:{x}px;top:{y}px" '
                         'onclick="send(event,\'target\')"></canvas>')
        else: boxes.append(button(x,y,'rgb(220,40,180)',name,'target'))
    if phase==2 and case in ('duplicate_visual','identity_swap'):
        dx=211+128*layout if case=='identity_swap' else x+44
        boxes.append(button(dx,y,'rgb(220,40,180)','Save','decoy'))
    if phase==2 and case in ('duplicate_native','semantic_conflict'):
        boxes.append(button(x+100,y,'rgb(40,100,210)','Save','decoy'))
    if phase==2 and case=='occluded':
        boxes.append(f'<div style="position:absolute;left:{x-3}px;top:{y-3}px;width:28px;height:22px;'
                     'background:#333;z-index:10" onclick="send(event,\'occluder\')"></div>')
    return ('<!doctype html><meta charset="utf-8"><style>*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#182028}'
            'button,canvas{position:absolute;width:22px;height:16px;border:0;padding:0;border-radius:0;outline:none}'
            '</style>'+''.join(boxes)+f'''<script>
function send(e,kind){{e.stopPropagation();console.log('__SCORER__'+JSON.stringify({{token:{json.dumps(token)},kind,trusted:e.isTrusted,x:e.clientX,y:e.clientY}}))}}
document.body.addEventListener('click',e=>send(e,'background'));
const c=document.querySelector('canvas');if(c){{const z=c.getContext('2d');z.fillStyle='rgb(220,40,180)';z.fillRect(0,0,22,16)}}
</script>''')
