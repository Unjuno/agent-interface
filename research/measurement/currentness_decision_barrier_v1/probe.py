from contract import *

s=Scope('s','t')
b=Barrier()
b.install(Decision('d100',s,100))
before=b.use(s)
inv=b.invalidate(Invalidation('e1',s))
after=b.use(s)
print({'before':before,'invalidation':inv,'after':after})
assert after['status']=='STALE_POLICY_REFUSED', 'FAIL_STALE_POLICY_ESCAPE: high generation survives required += 1'
