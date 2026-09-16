import candidate
x='''xkb_keymap {\nxkb_keycodes "x" { minimum=8; maximum=255; <LFSH> = 50; <AD01> = 24; <RALT> = 108; };\nxkb_symbols "x" { key <LFSH> { [ Shift_L ] }; key <AD01> { symbols[Group1]= [ q, Q, at, Greek_OMEGA ] }; key <RALT> { [ ISO_Level3_Shift ] }; };\n};'''
p=candidate.prepare('@',x);assert p.strokes[0].code==24 and p.strokes[0].level==2 and p.level3_code==108
try:candidate.prepare('^',x);raise AssertionError('dead/non-direct unexpectedly accepted')
except candidate.Rejected:pass
print('PASS_CANDIDATE_STATIC')
