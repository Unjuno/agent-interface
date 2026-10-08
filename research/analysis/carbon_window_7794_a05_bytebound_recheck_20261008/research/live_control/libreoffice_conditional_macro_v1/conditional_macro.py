import json

def apply_if_expected(doc, name, expected_x, new_x):
    page = doc.getDrawPages().getByIndex(0)
    shape = None
    for i in range(page.getCount()):
        s = page.getByIndex(i)
        if getattr(s, 'Name', '') == name:
            shape = s
            break
    if shape is None:
        return json.dumps({'status':'MISSING'}, sort_keys=True)
    before = int(shape.getPosition().X)
    if before != int(expected_x):
        return json.dumps({'status':'REFUSED','before_x':before,'expected_x':int(expected_x)}, sort_keys=True)
    p = shape.getPosition(); p.X = int(new_x); shape.setPosition(p)
    after = int(shape.getPosition().X)
    return json.dumps({'status':'APPLIED','before_x':before,'after_x':after}, sort_keys=True)

g_exportedScripts = (apply_if_expected,)
