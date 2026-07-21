#!/usr/bin/python3

import os
import sys
import subprocess
import argparse
import importlib.util
import signal
import shutil
from pathlib import Path

# put to the parent directory to avoid infinite loops
LOG_DIR = ".."

DEFAULT_COMPILER_FLAGS = ["-O2", "-g", "-std=c++17"]
SANITIZER_FLAGS = [
    "-fsanitize=undefined",
    "-fsanitize=bounds",
    "-fsanitize=address",
]
STRESS_SCRIPT = '''#!/usr/bin/env python3
import subprocess
import sys


def executable(name):
    return name if "/" in name else f"./{name}"


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: stress.py SOLUTION BRUTE GENERATOR")

    solution, brute, generator = map(executable, sys.argv[1:])
    iteration = 1
    while True:
        generated = subprocess.run([generator], capture_output=True, check=True)
        test_input = generated.stdout
        solution_run = subprocess.run([solution], input=test_input, capture_output=True)
        brute_run = subprocess.run([brute], input=test_input, capture_output=True)

        if solution_run.returncode != 0 or brute_run.returncode != 0 or solution_run.stdout != brute_run.stdout:
            with open("input.in", "wb") as input_file:
                input_file.write(test_input)
            with open("output.out", "wb") as output_file:
                output_file.write(solution_run.stdout)
            with open("expected.out", "wb") as expected_file:
                expected_file.write(brute_run.stdout)
            print(f"Mismatch on test {iteration}. Saved input.in, output.out, and expected.out.")
            return 1

        print(f"Passed {iteration}", end="\\r", flush=True)
        iteration += 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _pid_file(contest_name):
    return os.path.join(LOG_DIR, f".{contest_name}.xeppelin.pid")


def _read_pid(contest_name):
    try:
        with open(_pid_file(contest_name), "r") as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def _is_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def start(contest_name):
    if importlib.util.find_spec("watchdog") is None:
        print("Could not start watcher: the 'watchdog' package is not installed.")
        return

    log_file = os.path.join(LOG_DIR, f"{contest_name}.log")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    existing_pid = _read_pid(contest_name)
    if existing_pid and _is_running(existing_pid):
        print(f"Contest '{contest_name}' is already being watched.")
        return

    process = subprocess.Popen(
        [sys.executable, "-m", "xeppelin.watcher", os.getcwd(), os.path.abspath(log_file)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    with open(_pid_file(contest_name), "w") as file:
        file.write(str(process.pid))
    print(f"Started watching for contest '{contest_name}'. Log file: {log_file}")


def init_contest(contest_name, last_problem, template):
    contest_directory = Path(contest_name)
    if contest_directory.exists():
        raise SystemExit(f"Cannot initialize contest: '{contest_name}' already exists.")

    template_path = Path(template)
    if not template_path.is_file():
        raise SystemExit(f"Template file not found: {template}")

    last_problem = last_problem.upper()
    if len(last_problem) != 1 or not "A" <= last_problem <= "Z":
        raise SystemExit("LAST_PROBLEM must be a letter from A to Z.")

    contest_directory.mkdir()
    moved_template = contest_directory / template_path.name
    shutil.move(str(template_path), moved_template)
    template_contents = moved_template.read_bytes()

    for codepoint in range(ord("A"), ord(last_problem) + 1):
        (contest_directory / f"{chr(codepoint)}.cpp").write_bytes(template_contents)

    (contest_directory / "input.in").touch()
    (contest_directory / "output.out").touch()
    stress_path = contest_directory / "stress.py"
    stress_path.write_text(STRESS_SCRIPT)
    stress_path.chmod(0o755)

    original_directory = Path.cwd()
    try:
        os.chdir(contest_directory)
        start(contest_name)
    finally:
        os.chdir(original_directory)

    print(f"Initialized contest '{contest_name}' with problems A-{last_problem}.")


def compile_problem(problem, debug=True, sanitize=True):
    source = Path(f"{problem}.cpp")
    if not source.is_file():
        raise SystemExit(f"Source file not found: {source}")

    command = ["g++"]
    if sanitize:
        command.extend(SANITIZER_FLAGS)
    command.extend(DEFAULT_COMPILER_FLAGS)
    if debug:
        command.append("-DDEBUG")
    command.extend(["-o", problem, str(source)])
    subprocess.run(command, check=True)


def run_problem(problem, should_compile=True, debug=True, sanitize=True):
    if should_compile:
        compile_problem(problem, debug, sanitize)

    executable = Path(problem)
    if not executable.is_file():
        raise SystemExit(f"Executable not found: {problem}")

    with open("input.in", "rb") as input_file, open("output.out", "wb") as output_file:
        subprocess.run([f"./{problem}"], stdin=input_file, stdout=output_file, check=True)


def stress(solution, brute, generator):
    if not Path("stress.py").is_file():
        raise SystemExit("stress.py not found. Run this command from an initialized contest directory.")
    subprocess.run([sys.executable, "stress.py", solution, brute, generator], check=True)


def stop(contest_name):
    pid = _read_pid(contest_name)
    if not pid or not _is_running(pid):
        print(f"No active watcher found for contest '{contest_name}'.")
        return

    os.kill(pid, signal.SIGTERM)
    os.remove(_pid_file(contest_name))
    print(f"Stopped watching for contest '{contest_name}'.")


def show(contest_name, duration=300, freeze_time=None, title=None, template_name: str = 'template'):
    import matplotlib.pyplot as plt
    import xeppelin.xeppelin_logging as xeppelin_logging

    log_file = os.path.join(LOG_DIR, f"{contest_name}.log")
    if not os.path.exists(log_file):
        print(f"No log file found for contest '{contest_name}'.")
        return

    with open(log_file, 'r') as f:
        log_lines = f.readlines()

    solved_times = xeppelin_logging.parse_solved_info(log_lines)
    contest_start = xeppelin_logging.find_contest_start(log_lines, template_name)
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

    init_parser = subparsers.add_parser(
        'init',
        help='Create and start a new contest directory',
        epilog='Example: xeppelin init icpc-wf E'
    )
    init_parser.add_argument('contest_name', help='Directory and contest name')
    init_parser.add_argument('last_problem', help='Last problem letter to create (A-Z)')
    init_parser.add_argument('--template', default='template.cpp',
                             help='Template file to move into the contest (default: template.cpp)')

    compile_parser = subparsers.add_parser('compile', help='Compile a C++ problem')
    compile_parser.add_argument('problem', help='Problem name, for example E')
    compile_parser.add_argument('--no-debug', action='store_true', help='Do not define DEBUG')
    compile_parser.add_argument('--no-sanitize', action='store_true', help='Disable sanitizers')

    run_parser = subparsers.add_parser('run', help='Compile and run a problem')
    run_parser.add_argument('problem', help='Problem name, for example E')
    run_parser.add_argument('--no-compile', action='store_true', help='Run the existing binary')
    run_parser.add_argument('--no-debug', action='store_true', help='Do not define DEBUG when compiling')
    run_parser.add_argument('--no-sanitize', action='store_true', help='Disable sanitizers when compiling')

    stress_parser = subparsers.add_parser('stress', help='Stress test two existing binaries')
    stress_parser.add_argument('solution', help='Solution binary')
    stress_parser.add_argument('brute', help='Brute-force binary')
    stress_parser.add_argument('generator', help='Generator binary')

    from xeppelin import edulcni as edulcni_command
    edulcni_command.add_parser(subparsers)

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
  xeppelin show icpc-wf --template main
  xeppelin show icpc-wf --duration 300 --freeze 240 --template main --title "ICPC World Finals"'''
    )
    show_parser.add_argument('contest_name',
                            help='Name of the contest to visualize. Should match the name used with the start command.')
    show_parser.add_argument('--duration', type=int, default=300,
                            help='Maximum time (in minutes) to show on the visualization axis (default: 300)')
    show_parser.add_argument('--freeze', type=str, default=240,
                            help='Add a freeze period indicator starting at specified time (format: HH:MM or minutes as integer)')
    show_parser.add_argument('--template', type=str, default='template',
                             help='Name of the template file (default: template)')
    # show_parser.add_argument('--problemset', type=str, default='abcdefghijklmno')
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
    if args.command == 'init':
        init_contest(args.contest_name, args.last_problem, args.template)
    elif args.command == 'compile':
        compile_problem(args.problem, not args.no_debug, not args.no_sanitize)
    elif args.command == 'run':
        run_problem(args.problem, not args.no_compile, not args.no_debug, not args.no_sanitize)
    elif args.command == 'stress':
        stress(args.solution, args.brute, args.generator)
    elif args.command == 'edulcni':
        edulcni_command.run_from_args(args)
    elif args.command == 'start':
        start(args.contest_name)
    elif args.command == 'stop':
        stop(args.contest_name)
    elif args.command == 'show':
        show(args.contest_name, args.duration, args.freeze, args.title, args.template)
    elif args.command == 'log':
        log_submissions(args.contest_name, args.submission_info)

if __name__ == "__main__":
    main()
