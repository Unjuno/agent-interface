"""Cross-heading wrapper around the exact retained #733 v2 fixture."""
import sys,time
import vizdoom as vd
import base_fixture as base

def _pop_heading(argv):
    if '--heading' not in argv:
        return None
    i=argv.index('--heading')
    if i+1>=len(argv):
        raise SystemExit('--heading requires a value')
    value=float(argv[i+1])
    del argv[i:i+2]
    return value

HEADING=_pop_heading(sys.argv)
_ORIGINAL_ALIGN=base.align_boundary

def _align_boundary(g,inp,line_id):
    row=_ORIGINAL_ALIGN(g,inp,line_id)
    if HEADING is None:
        row.update(requested_heading=None,actual_heading=row['angle'],heading_error=None)
        return row
    for _ in range(32):
        ang=float(g.get_game_variable(vd.GameVariable.ANGLE))
        err=base.derr(HEADING,ang)
        if abs(err)<8:
            break
        inp.press('Left' if err>0 else 'Right',.19,.01,'setup_heading')
        time.sleep(.08);g.advance_action(1,True);time.sleep(.02)
    ang=float(g.get_game_variable(vd.GameVariable.ANGLE));err=base.derr(HEADING,ang)
    row.update(angle=ang,desired_angle=HEADING,angle_error=err,
               requested_heading=float(HEADING),actual_heading=ang,heading_error=err)
    return row

base.align_boundary=_align_boundary

if __name__=='__main__':
    base.main()
