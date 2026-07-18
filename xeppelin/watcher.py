import argparse
import signal
import threading
from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ModificationLogger(FileSystemEventHandler):
    def __init__(self, watch_directory, log_file):
        self.watch_directory = watch_directory
        self.log_file = log_file

    def on_modified(self, event):
        if event.is_directory:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        relative_path = Path(event.src_path).relative_to(self.watch_directory)
        with open(self.log_file, "a") as file:
            file.write(f"{timestamp} - ./{relative_path} was modified\n")


def watch(watch_directory, log_file):
    watch_directory = Path(watch_directory).resolve()
    stopped = threading.Event()
    observer = Observer()
    observer.schedule(
        ModificationLogger(watch_directory, log_file),
        str(watch_directory),
        recursive=True,
    )

    def stop_watching(_signal_number, _frame):
        stopped.set()

    signal.signal(signal.SIGTERM, stop_watching)
    signal.signal(signal.SIGINT, stop_watching)

    observer.start()
    try:
        stopped.wait()
    finally:
        observer.stop()
        observer.join()


def main():
    parser = argparse.ArgumentParser(description="Xeppelin file watcher")
    parser.add_argument("watch_directory")
    parser.add_argument("log_file")
    args = parser.parse_args()
    watch(args.watch_directory, args.log_file)


if __name__ == "__main__":
    main()
