#!/bin/bash

# Directory to watch
WATCH_DIR="."

# Log file passed as an argument
LOG_FILE="$1"

# Ensure inotify-tools is installed
if ! command -v inotifywait &> /dev/null; then
    echo "Error: inotifywait is not installed. Install it using: sudo apt install inotify-tools" >&2
    exit 1
fi

# Start watching the directory
echo "Watching $WATCH_DIR for modifications..."
inotifywait -m -r -e modify "$WATCH_DIR" | while read file_path file_event file_name; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$TIMESTAMP - $file_path$file_name was modified" >> "$LOG_FILE"
    # echo "Logged modification at $TIMESTAMP"
done
