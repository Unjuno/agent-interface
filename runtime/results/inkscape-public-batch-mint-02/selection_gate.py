# Application-specific read-only rule; no action authority or generic selection claim.
BOXES=((320,301,336,315),(350,273,364,291),(350,324,364,342))
def selection_state(rgb, geometry_state):
 if rgb.mode!='RGB' or rgb.size!=(1000,700) or geometry_state!='initial':return 'unknown'
 fractions=[]
 for box in BOXES:
  pixels=list(rgb.crop(box).getdata());fractions.append(sum(max(v)<40 for v in pixels)/len(pixels))
 if all(v>=.20 for v in fractions):return 'selected'
 if all(v<=.01 for v in fractions):return 'unselected'
 return 'unknown'
