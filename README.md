# Xeppelin Contest Watcher

Xeppelin is a contest watcher software that keeps track of file modifications during a contest and creates visualizations of your activity.

## Installation

```
pip install xeppelin
```

## Commands

- **Start Watching**:   ```
  xeppelin start <contest_name>  ```
  Starts watching the current directory for file modifications and logs them to `<contest_name>.log`.

- **Stop Watching**:   ```
  xeppelin stop <contest_name>  ```
  Stops watching for the specified contest.

- **Show Visualization**:   ```
  xeppelin show <contest_name>  ```
  Displays a visualization of the activities logged for the specified contest.

- **Log Submissions**:   ```
  xeppelin log-submissions <contest_name> <submission_info>  ```
  Adds additional submission information to the log file for the specified contest.
  Usually should be used to log the time of the submission.
  Example:
  ```
  xeppelin log-submissions test "A solved 1:30"
  ```

## Format

All problems are coded in files named `A.cpp`, `B.cpp`, etc.
The compiled binary is named `A`, `B`, etc.
Some additional files for the contest (stress-testing, additional solutions, etc.) are also allowed, if their filename starts with letter that matches the problem letter.

## Requirements

- `inotify-tools` for file watching.
- Python packages: `pandas`, `matplotlib`, `numpy`.
- Verified to work on Ubuntu and WSL2.

```
sudo apt install inotify-tools

pip install pandas matplotlib numpy
```
