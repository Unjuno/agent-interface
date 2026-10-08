"""Independent, deliberately bounded SVG fixture scorer; never a control API."""
from decimal import Decimal,InvalidOperation
import re,xml.etree.ElementTree as ET

SVG='{http://www.w3.org/2000/svg}'
INK='{http://www.inkscape.org/namespaces/inkscape}'
SOD='{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}'
class Unsupported(ValueError):pass
def number(value):
    try:n=Decimal(value)
    except (InvalidOperation,TypeError):raise Unsupported('unitless finite number required')
    if not n.is_finite():raise Unsupported('nonfinite number')
    return n
def color(value):
    value=value.lower();value={'red':'#ff0000','blue':'#0000ff','green':'#008000','black':'#000000','white':'#ffffff','none':'none'}.get(value,value)
    if re.fullmatch('#[0-9a-f]{3}',value):value='#'+''.join(c*2 for c in value[1:])
    if value!='none' and not re.fullmatch('#[0-9a-f]{6}',value):raise Unsupported('unsupported fill syntax')
    return value
def snapshot(text):
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():raise Unsupported('declarations outside fixture contract')
    try:root=ET.fromstring(text)
    except ET.ParseError as exc:raise Unsupported('malformed XML') from exc
    if root.tag!=SVG+'svg':raise Unsupported('SVG root required')
    allowed={'width','height','viewBox','version','id',SOD+'docname',INK+'version'}
    if set(root.attrib)-allowed:raise Unsupported('unsupported root attribute')
    if root.text and root.text.strip():raise Unsupported('root text outside contract')
    viewport=tuple(number(root.get(k)) for k in ('width','height'))
    viewbox=tuple(number(v) for v in root.get('viewBox','').split())
    if len(viewbox)!=4:raise Unsupported('four-value viewBox required')
    rects=[];ids=set()
    for node in root:
        if node.tail and node.tail.strip():raise Unsupported('non-whitespace tail')
        if node.tag==SOD+'namedview':continue # Explicit editor-state exclusion.
        if node.tag==SVG+'defs' and len(node)==0 and not (node.text or '').strip() and set(node.attrib)<={'id'}:continue
        if node.tag!=SVG+'rect' or len(node) or (node.text or '').strip():raise Unsupported('only flat rectangles supported')
        if set(node.attrib)-{'id','x','y','width','height','fill','opacity'}:raise Unsupported('unsupported rectangle attribute')
        ident=node.get('id')
        if not ident or ident in ids:raise Unsupported('unique rectangle IDs required')
        ids.add(ident)
        rects.append({'id':ident,**{k:number(node.get(k,'0')) for k in ('x','y','width','height')},'fill':color(node.get('fill','black')),'opacity':number(node.get('opacity','1'))})
    return dict(viewport=viewport,viewbox=viewbox,rects=rects)
def evaluate(before,after,contract):
    if set(contract)!={'target_id','required_dx_screen','pixels_per_svg_unit','tolerance_screen'}:raise ValueError('invalid oracle contract fields')
    scale=number(str(contract['pixels_per_svg_unit']));tolerance=number(str(contract['tolerance_screen']));target=contract['target_id']
    if scale<=0 or tolerance<0:raise ValueError('invalid scale/tolerance')
    required=number(str(contract['required_dx_screen']))
    try:a,b=snapshot(before),snapshot(after)
    except Unsupported as exc:return dict(evaluation_supported=False,success=False,reason=str(exc))
    old=next((r for r in a['rects'] if r['id']==target),None);new=next((r for r in b['rects'] if r['id']==target),None)
    if old is None:raise ValueError('target absent from initial fixture')
    dx=None if new is None else (new['x']-old['x'])*scale
    required_ok=dx is not None and abs(dx-required)<=tolerance
    # Compare every supported render attribute, object order/count and viewport,
    # allowing only the target x attribute to differ.
    if new is not None:new['x']=old['x']
    collateral_ok=a==b
    return dict(evaluation_supported=True,success=required_ok and collateral_ok,
                required_effect=required_ok,collateral_preserved=collateral_ok,
                dx_screen=None if dx is None else float(dx),
                scope='all declared flat-rectangle render attributes/order and viewport; editor metadata excluded')
