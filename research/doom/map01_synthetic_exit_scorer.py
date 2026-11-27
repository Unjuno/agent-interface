"""Private, passive start and terminal observations for the synthetic exit calibration."""
import math,time
from map01_door_sector_scorer import DoorSectorScorer

class SyntheticExitScorer(DoorSectorScorer):
    def __init__(self,path,*,clock=time.perf_counter_ns):
        super().__init__(path,clock=clock,traverse=True,exit_probe=True)
        self.STAGES=('cover-0','exit-probe')

    def sample(self,stage,game,terminal_ns,physical_neutral):
        if stage=='exit-probe':
            return self._terminal_sample(game,terminal_ns,physical_neutral)
        if stage!='cover-0':
            raise ValueError('unexpected synthetic stage')
        if self.failed or self.index!=0:raise ValueError('unexpected synthetic start stage')
        attempted=returned=False
        try:
            from vizdoom import GameVariable as V
            started=self.clock()
            if (type(started) is not int or type(terminal_ns) is not int
                    or not 0<=started-terminal_ns<=1_000_000_000
                    or not callable(physical_neutral) or physical_neutral() is not True
                    or list(game.get_last_action())!=[0.0]*9):
                raise ValueError('start neutral evidence unavailable')
            before=game.get_episode_time()
            checked=self.clock()
            if type(checked) is not int or not started<=checked<=terminal_ns+1_000_000_000:
                raise ValueError('start refresh deadline expired')
            self._refresh_record({'event':'attempt','observed_ns':checked,'tic_before':before})
            after_log=self.clock()
            if type(after_log) is not int or not checked<=after_log<=terminal_ns+1_000_000_000:
                self._refresh_record({'event':'expired_before_call','observed_ns':after_log})
                raise ValueError('start refresh deadline expired after logging')
            attempted=True
            game.advance_action(1,True)
            returned=True
            self._refresh_record({'event':'returned','observed_ns':self.clock()})
            tic=game.get_episode_time();finished=game.is_episode_finished();dead=game.is_player_dead()
            timeout=getattr(game,'is_episode_timeout_reached',None)
            timeout=timeout() if callable(timeout) else None
            values=[game.get_game_variable(v) for v in (V.POSITION_X,V.POSITION_Y,V.ANGLE,V.HEALTH,V.DEATHCOUNT)]
            state=game.get_state();tic_after=game.get_episode_time();neutral=physical_neutral() is True
            action=list(game.get_last_action());ended=self.clock()
            if (type(before) is not int or type(tic) is not int or not 0<=before<tic or type(tic_after) is not int or tic!=tic_after
                    or finished is not False or dead is not False or timeout is not False
                    or any(type(value) not in (int,float) or not math.isfinite(value) for value in values)
                    or values!=[80.0,0.0,0.0,100.0,0.0] or state is None or getattr(state,'tic',None)!=tic
                    or not neutral or action!=[0.0]*9 or type(ended) is not int
                    or not started<=ended<=terminal_ns+1_000_000_000):
                raise ValueError('synthetic initial state differs')
            self._write({'schema':'synthetic-exit-start-sample-v1','status':'observed','stage':stage,
                'started_ns':started,'finished_ns':ended,'terminal_ns':terminal_ns,'tic_before':before,'tic':tic,
                'position_x':values[0],'position_y':values[1],'angle':values[2],
                'health':values[3],'death_count':0,'episode_finished':False,'player_dead':False,
                'native_timeout':False,'physical_neutral_before_after':True,'refresh_count':1})
            self.index+=1
        except Exception as error:
            self.failed=True
            self._write({'schema':'synthetic-exit-start-sample-v1','status':'HOLD','stage':stage,
                         'refresh_attempted':attempted,'refresh_returned':returned,
                         'error_type':type(error).__name__})
            raise

    def _refresh_record(self,row):
        import json,os
        with self.path.with_name(self.path.name+'.refresh.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            stream.flush();os.fsync(stream.fileno())

    def _terminal_sample(self,game,terminal_ns,physical_neutral):
        if self.failed or self.index!=1:raise ValueError('unexpected synthetic terminal stage')
        try:
            from vizdoom import GameVariable as V
            started=self.clock()
            if (type(started) is not int or type(terminal_ns) is not int
                    or not 0<=started-terminal_ns<=1_000_000_000
                    or not callable(physical_neutral) or physical_neutral() is not True):
                raise ValueError('terminal physical neutral unavailable')
            tic=game.get_episode_time();finished=game.is_episode_finished();dead=game.is_player_dead()
            timeout=getattr(game,'is_episode_timeout_reached',None)
            timeout=timeout() if callable(timeout) else None
            deaths=game.get_game_variable(V.DEATHCOUNT)
            action=list(game.get_last_action())
            finished_again=game.is_episode_finished();tic_after=game.get_episode_time()
            neutral_after=physical_neutral() is True;action_after=list(game.get_last_action());ended=self.clock()
            if (type(tic) is not int or tic<0 or type(tic_after) is not int or tic!=tic_after
                    or type(finished) is not bool or finished_again is not finished or type(dead) is not bool
                    or type(timeout) is not bool or type(deaths) not in (int,float)
                    or not math.isfinite(deaths) or deaths<0 or deaths%1!=0
                    or len(action)!=9 or any(type(x) not in (int,float) or not math.isfinite(x) for x in action)
                    or action_after!=action or not neutral_after or type(ended) is not int
                    or not started<=ended<=terminal_ns+1_000_000_000):
                raise ValueError('synthetic terminal facts unavailable')
            self._write({'schema':'synthetic-exit-terminal-sample-v1','status':'terminal_probe_observed',
                'stage':'exit-probe','started_ns':started,'finished_ns':ended,'terminal_ns':terminal_ns,
                'tic_before':tic,'tic_after':tic_after,'episode_finished':finished,'player_dead':dead,
                'native_timeout':timeout,'death_count':int(deaths),'engine_last_action':action,
                'physical_neutral_before_after':True,'refresh_count':0})
            self.index+=1
        except Exception as error:
            self.failed=True
            self._write({'schema':'synthetic-exit-terminal-sample-v1','status':'HOLD',
                         'stage':'exit-probe','error_type':type(error).__name__})
            raise
