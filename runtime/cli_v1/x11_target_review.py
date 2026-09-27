"""Read-only focused-client evidence for explicit persistent X11 target review.

WM properties are application metadata, not authenticated identity. This does not
prove visual freshness or authorize input; ordinary dispatch admission remains.
"""
def inspect_focused_target(backend, family_root):
    from Xlib import X
    d, root = backend.d, backend.root
    prop = root.get_full_property(d.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
    if prop is None or prop.format != 32 or len(prop.value) > 4096:
        raise ValueError('managed client inventory unavailable or too large')
    managed = {int(x) for x in prop.value}
    focus = d.get_input_focus().focus
    focus_path = []
    for _ in range(64):
        wid = getattr(focus, 'id', None)
        if not wid or wid in focus_path:
            raise ValueError('focused managed client unavailable')
        focus_path.append(wid)
        if wid in managed:
            break
        focus = focus.query_tree().parent
    else:
        raise ValueError('focus ancestry exceeds limit')
    win = focus
    if win.get_attributes().map_state != X.IsViewable:
        raise ValueError('focused client is not viewable')
    chain = [win.id]
    current = win
    for _ in range(16):
        if current.id == family_root:
            break
        current = current.get_wm_transient_for()
        if current is None or current.id in chain:
            raise ValueError('focused client is outside configured transient family')
        chain.append(current.id)
    else:
        raise ValueError('transient ancestry exceeds limit')
    geo = win.get_geometry()
    point = root.translate_coords(win, 0, 0)
    title = win.get_wm_name()
    if isinstance(title, bytes):
        title = title.decode('utf-8', 'replace')
    return {'window_id': win.id, 'focus_path': focus_path,
            'transient_chain': chain, 'family_root': family_root,
            'title': title, 'wm_class': list(win.get_wm_class() or ()),
            'geometry': [point.x, point.y, geo.width, geo.height]}