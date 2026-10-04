import subprocess

def retire_process(process,grace_seconds=5):
 r={'initial_exit':process.poll(),'steps':[],'errors':[]}
 if process.stdin is not None:
  try:process.stdin.close();r['steps'].append('stdin_closed')
  except Exception as e:r['errors'].append({'step':'stdin_close','error':repr(e)})
 for step,action in [('grace',None),('terminate',process.terminate),('kill',process.kill)]:
  if action is not None and process.poll() is None:
   try:action();r['steps'].append(step)
   except Exception as e:r['errors'].append({'step':step,'error':repr(e)})
  try:process.wait(timeout=grace_seconds);break
  except subprocess.TimeoutExpired:r['steps'].append(step+'_timeout')
  except Exception as e:r['errors'].append({'step':step+'_wait','error':repr(e)})
 r['final_exit']=process.poll();r['terminal']=r['final_exit'] is not None
 return r
