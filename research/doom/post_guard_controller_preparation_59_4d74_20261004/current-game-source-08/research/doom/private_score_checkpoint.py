"""Prospective scoring-only checkpoint; never returns scores to controller."""
import time,json

def checkpoint(game,executor,owner,variables,log_path,checkpoint_id):
 row={'schema':'private-score-checkpoint-v1','id':checkpoint_id,'started_ns':time.perf_counter_ns(),'status':'UNKNOWN','grants_input_authority':False}
 try:
  with executor.lock:
   if executor.closed or executor.active is not None:raise ValueError('scoring requires idle open executor')
   state=owner.call('input_state')
   if state['owned_keycodes'] or state['owned_buttons'] or state['active_lease_deadline_ns'] is not None:raise ValueError('owner is not neutral')
   row['owner_state']=state
   # This state checks tracked owner holds, not all physical keys. Independent
   # per-key terminal release must be audited separately before grading.
   if game.is_episode_finished():raise ValueError('finished episode cannot refresh')
   row['refresh_before_ns']=time.perf_counter_ns();row['tic_before']=game.get_episode_time()
   game.advance_action(1,True)
   row['refresh_after_ns']=time.perf_counter_ns();row['tic_after']=game.get_episode_time()
   row['values']={name:game.get_game_variable(variable) for name,variable in variables.items()}
   row['read_finished_ns']=time.perf_counter_ns();row['tic_after_read']=game.get_episode_time()
   row['status']='REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING'
 except Exception as error:row['error']=repr(error)
 finally:
  row['finished_ns']=time.perf_counter_ns()
  with log_path.open('a') as log:log.write(json.dumps(row)+'\n')
 return {'checkpoint_id':checkpoint_id,'status':row['status']} # no score values
