#!/usr/bin/python3

import os
import sys
import subprocess
import argparse
from datetime import datetime
import xeppelin.xeppelin_logging as xeppelin_logging
import matplotlib.pyplot as plt
import pkg_resources

# put to the parent directory to avoid infinite loops
LOG_DIR = ".."

def start(contest_name):
    log_file = os.path.join(LOG_DIR, f"{contest_name}.log")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Use pkg_resources to find the script path
    script_path = pkg_resources.resource_filename('xeppelin', 'xeppelin.sh')
    
    # Start the xeppelin.sh script in the background
    subprocess.Popen([script_path, log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Started watching for contest '{contest_name}'. Log file: {log_file}")

def stop(contest_name):
    # Find and kill the process
    subprocess.run(["pkill", "xeppelin.sh"])
    print(f"Stopped watching for contest '{contest_name}'.")

def show(contest_name, duration=300, freeze_time=None, title=None):
    log_file = os.path.join(LOG_DIR, f"{contest_name}.log")
    if not os.path.exists(log_file):
        print(f"No log file found for contest '{contest_name}'.")
        return
    
    with open(log_file, 'r') as f:
        log_lines = f.readlines()
    
    solved_times = xeppelin_logging.parse_solved_info(log_lines)
    contest_start = xeppelin_logging.find_contest_start(log_lines)
    if not contest_start:
        print("Could not find contest start!")
        return
        
    activities = xeppelin_logging.group_activities(log_lines, contest_start)
    fig = xeppelin_logging.plot_activities(contest_name if title is None else title, activities, solved_times, duration, freeze_time)
    fig.savefig(os.path.join(LOG_DIR, f"{contest_name}.png"))
    plt.show()

def log_submissions(contest_name, submission_info):
    log_file = os.path.join(LOG_DIR, f"{contest_name}.log")
    with open(log_file, 'a') as f:
        f.write(f"{submission_info}\n")
    print(f"Logged submission info for contest '{contest_name}'.")

def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(
        description='Xeppelin contest watcher utility - monitors and visualizes programming contest activities',
        epilog='For more information, visit: https://github.com/KiK0s/xeppelin'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create parser for "start" command
    start_parser = subparsers.add_parser(
        'start', 
        help='Start watching the current directory for a contest',
        description='Start monitoring the current directory for contest activities. This command will track file modifications and log them for later visualization.',
        epilog='Example: xeppelin start icpc-wf'
    )
    start_parser.add_argument('contest_name', 
                             help='Name of the contest to start watching. This will be used for the log file name.')
    
    # Create parser for "stop" command
    stop_parser = subparsers.add_parser(
        'stop', 
        help='Stop watching for a contest',
        description='Stop monitoring the specified contest and terminate the file watching process.',
        epilog='Example: xeppelin stop icpc-wf'
    )
    stop_parser.add_argument('contest_name', 
                            help='Name of the contest to stop watching. Should match the name used with the start command.')
    
    # Create parser for "show" command
    show_parser = subparsers.add_parser(
        'show', 
        help='Display visualization of contest activities',
        description='Generate and display a visualization of contest activities from the log file. This shows your coding activity timeline and problem submissions.',
        epilog='''Examples:
  xeppelin show icpc-wf
  xeppelin show icpc-wf --duration 240
  xeppelin show icpc-wf --freeze 4:00
  xeppelin show icpc-wf --duration 300 --freeze 240 --title "ICPC World Finals"'''
    )
    show_parser.add_argument('contest_name', 
                            help='Name of the contest to visualize. Should match the name used with the start command.')
    show_parser.add_argument('--duration', type=int, default=300, 
                            help='Maximum time (in minutes) to show on the visualization axis (default: 300)')
    show_parser.add_argument('--freeze', type=str, default=None, 
                            help='Add a freeze period indicator starting at specified time (format: HH:MM or minutes as integer)')
    show_parser.add_argument('--title', type=str, default=None,
                            help='Custom title for the visualization (default: contest name)')
    
    # Create parser for "log" command
    log_parser = subparsers.add_parser(
        'log', 
        help='Log submission information for a contest',
        description='Manually add submission information to the contest log file. Use this to record when problems were solved.',
        epilog='Example: xeppelin log icpc-wf "A solved 1:30"'
    )
    log_parser.add_argument('contest_name', 
                           help='Name of the contest to log submissions for')
    log_parser.add_argument('submission_info', 
                           help='Submission information to log (e.g., "A solved 1:30" means problem A was solved at 1 hour and 30 minutes)')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Execute the appropriate command
    if args.command == 'start':
        start(args.contest_name)
    elif args.command == 'stop':
        stop(args.contest_name)
    elif args.command == 'show':
        show(args.contest_name, args.duration, args.freeze, args.title)
    elif args.command == 'log':
        log_submissions(args.contest_name, args.submission_info)

if __name__ == "__main__":
    main() 