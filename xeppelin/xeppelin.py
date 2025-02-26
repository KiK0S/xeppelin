#!/usr/bin/python3

import os
import sys
import subprocess
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

def show(contest_name):
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
    fig = xeppelin_logging.plot_activities(contest_name, activities, solved_times)
    fig.savefig(os.path.join(LOG_DIR, f"{contest_name}.png"))
    plt.show()

def log_submissions(contest_name, submission_info):
    log_file = os.path.join(LOG_DIR, f"{contest_name}.log")
    with open(log_file, 'a') as f:
        f.write(f"{submission_info}\n")
    print(f"Logged submission info for contest '{contest_name}'.")

def main():
    if len(sys.argv) < 3:
        print("Usage: xeppelin <command> <contest_name> [additional_args]")
        return
    
    command = sys.argv[1]
    contest_name = sys.argv[2]
    
    if command == "start":
        start(contest_name)
    elif command == "stop":
        stop(contest_name)
    elif command == "show":
        show(contest_name)
    elif command == "log":
        if len(sys.argv) < 4:
            print("Usage: xeppelin log <contest_name> <submission_info>")
            return
        submission_info = sys.argv[3]
        log_submissions(contest_name, submission_info)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main() 