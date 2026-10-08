def observe_dead(expected_ticks,read,clock,sleep,timeout_ns,poll_ns):
    started=clock();samples=[]
    while True:
        before=clock();state,ticks=read();at=clock()
        samples.append({"query_started_ns":before,"at_ns":at,"state":state,"start_ticks":ticks})
        if state!="missing" and ticks!=expected_ticks:raise ValueError("STOP_OWNER_GENERATION_CHANGED: "+repr(samples))
        if at-started>timeout_ns:raise ValueError("STOP_OWNER_DEATH_TIMEOUT: "+repr(samples))
        if state in ("Z","missing"):
            return {"started_ns":started,"at_ns":at,"state":state,"start_ticks":ticks,"samples":samples}
        sleep(poll_ns)
