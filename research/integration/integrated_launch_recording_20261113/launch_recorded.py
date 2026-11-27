"""Run an existing launcher inside the outer attempt boundary."""
import argparse
from pathlib import Path
import runpy
from record_launch import record_launch

def launch_recorded(launcher, attempt_directory):
    # Resolve/read launcher and its conditions inside the recorded boundary.
    return record_launch(attempt_directory,
        lambda: runpy.run_path(str(Path(launcher).resolve()), run_name='__main__'),
        planned_stages=['condition_validation','host_start','application_start',
                        'model_and_task','scoring','cleanup'])

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('launcher')
    parser.add_argument('attempt_directory')
    args=parser.parse_args()
    launch_recorded(args.launcher,args.attempt_directory)
