"""Private, post-release sector observations for the finite door trial.

Records raw plane coefficients and their sum for a known horizontal sector.
This recorder does not determine causality or authorize controller input.
"""
import json
import math
import os
import time
from pathlib import Path


class DoorSectorScorer:
    STAGES=('cover-0','approach-1','approach-2','approach-3','approach-4','intervention')
    TARGET={frozenset(((704.0,-96.0),(704.0,-224.0))),
            frozenset(((720.0,-96.0),(720.0,-224.0)))}

    def __init__(self, path, *, clock=time.perf_counter_ns, traverse=False):
        if type(traverse) is not bool:raise ValueError('invalid traversal mode')
        self.traverse=traverse
        self.STAGES=type(self).STAGES+(('traverse-1',) if traverse else ())
        self.path=Path(path)
        self.clock=clock
        self.index=0
        self.last_tic=None
        self.last_state_number=None
        self.failed=False
        descriptor=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(descriptor,'w',encoding='utf-8') as stream:
            stream.flush()
            os.fsync(stream.fileno())

    def _write(self,row):
        with self.path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            stream.flush()
            os.fsync(stream.fileno())

    def sample(self, stage, game, terminal_ns, physical_neutral):
        if self.failed or self.index>=len(self.STAGES) or stage!=self.STAGES[self.index]:
            raise ValueError('unexpected sector sample stage')
        attempted=returned=False
        try:
            started=self.clock()
            if (type(started) is not int or type(terminal_ns) is not int
                    or not 0<=started-terminal_ns<=1_000_000_000
                    or not callable(physical_neutral) or physical_neutral() is not True
                    or list(game.get_last_action())!=[0.0]*9):
                raise ValueError('scorer refresh requires fresh physical neutral input')
            before=game.get_episode_time()
            refresh_started=self.clock()
            if type(refresh_started) is not int or not started<=refresh_started<=terminal_ns+1_000_000_000:
                raise ValueError('sector refresh window expired')
            attempted=True
            game.advance_action(1,True)
            returned=True
            getter_before=game.get_episode_time()
            state=game.get_state()
            getter_after=game.get_episode_time()
            finished=self.clock()
            if (state is None or type(before) is not int or type(getter_before) is not int
                    or type(getter_after) is not int or type(getattr(state,'tic',None)) is not int
                    or type(getattr(state,'number',None)) is not int
                    or type(finished) is not int
                    or not refresh_started<=finished<=terminal_ns+1_000_000_000
                    or not before<getter_before==state.tic==getter_after
                    or self.last_tic is not None and state.tic<=self.last_tic
                    or self.last_state_number is not None and state.number<=self.last_state_number
                    or physical_neutral() is not True or list(game.get_last_action())!=[0.0]*9):
                raise ValueError('sector sample is stale or non-neutral')
            matches=[]
            for index,sector in enumerate(state.sectors):
                lines={frozenset(((float(line.x1),float(line.y1)),(float(line.x2),float(line.y2))))
                       for line in sector.lines}
                if self.TARGET.issubset(lines):
                    floor=float(sector.floor_height);ceiling=float(sector.ceiling_height)
                    if not math.isfinite(floor) or not math.isfinite(ceiling):
                        raise ValueError('sector coefficients are non-finite')
                    matches.append((index,floor,ceiling))
            if len(matches)!=1:
                raise ValueError('door sector is missing or ambiguous')
            sector,floor,ceiling=matches[0]
            position={}
            if self.traverse:
                values=getattr(state,'game_variables',None)
                if values is None or len(values)!=6 or not all(math.isfinite(float(value)) for value in values):
                    raise ValueError('same-state position or health unavailable')
                death,kills,x,y,angle,health=map(float,values)
                position={'death_count':death,'kill_count':kills,'position_x':x,'position_y':y,'angle':angle,'health':health}
            self._write(dict(position,**{'schema':'map01-door-sector-sample-v1','status':'observed','stage':stage,
                         'started_ns':started,'finished_ns':finished,'terminal_ns':terminal_ns,
                         'terminal_to_sample_ns':started-terminal_ns,
                         'terminal_to_refresh_ns':refresh_started-terminal_ns,
                         'terminal_to_state_ns':finished-terminal_ns,'tic_before':before,
                         'getter_before_state':getter_before,'state_tic':state.tic,
                         'state_number':state.number,'getter_after_state':getter_after,
                         'refresh_count':1,'physical_neutral_before_after':True,
                         'last_action':[0.0]*9,'sector_index':sector,
                         'floor_d':floor,'ceiling_d':ceiling,'gap':floor+ceiling}))
            self.last_tic=state.tic
            self.last_state_number=state.number
            self.index+=1
        except Exception as error:
            self.failed=True
            self._write({'schema':'map01-door-sector-sample-v1','status':'HOLD','stage':stage,
                         'refresh_attempted':attempted,'refresh_returned':returned,
                         'error_type':type(error).__name__})
            raise
