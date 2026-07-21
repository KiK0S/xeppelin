import os
import secrets
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path


READY_PREFIX = "EDULCNI_READY "
DEFAULT_READY_TIMEOUT_SECONDS = 10.0
DEFAULT_COMPILER_FLAGS = ["-O2", "-g", "-std=c++17"]
SANITIZER_FLAGS = [
    "-fsanitize=undefined",
    "-fsanitize=bounds",
    "-fsanitize=address",
]


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "edulcni",
        help="Compile and run a problem with the native Edulcni viewer",
    )
    parser.add_argument("problem", help="Problem name, for example A")
    parser.add_argument("--input", default="input.in", help="Input file (default: input.in)")
    parser.add_argument("--output", default="output.out", help="Output file (default: output.out)")
    parser.add_argument("--no-debug", action="store_true", help="Do not define DEBUG")
    parser.add_argument("--no-sanitize", action="store_true", help="Disable sanitizers")
    parser.add_argument("--compiler", default=os.environ.get("CXX", "g++"), help="C++ compiler")
    parser.add_argument(
        "--edulcni-root",
        help="Edulcni checkout/install root (or set EDULCNI_ROOT)",
    )
    parser.add_argument(
        "--viewer",
        help="Native viewer executable (or set EDULCNI_VIEWER)",
    )
    parser.add_argument(
        "--include-dir",
        help="Edulcni include directory (or set EDULCNI_INCLUDE_DIR)",
    )
    parser.add_argument(
        "--library-dir",
        help="Directory containing libedulcni (or set EDULCNI_LIBRARY_DIR)",
    )
    parser.add_argument(
        "--bootstrap",
        default=os.environ.get("EDULCNI_BOOTSTRAP", "edulcni/bootstrap.hpp"),
        help="Header force-included in the instrumented build",
    )
    parser.add_argument(
        "--extra-compile-flag",
        action="append",
        default=[],
        help="Additional compiler flag; may be repeated",
    )
    parser.add_argument(
        "--extra-link-flag",
        action="append",
        default=[],
        help="Additional linker flag; may be repeated",
    )
    return parser


def run_from_args(args):
    run(
        problem=args.problem,
        input_path=Path(args.input),
        output_path=Path(args.output),
        compiler=args.compiler,
        debug=not args.no_debug,
        sanitize=not args.no_sanitize,
        edulcni_root=args.edulcni_root,
        viewer=args.viewer,
        include_dir=args.include_dir,
        library_dir=args.library_dir,
        bootstrap=args.bootstrap,
        extra_compile_flags=args.extra_compile_flag,
        extra_link_flags=args.extra_link_flag,
    )


def run(
    problem,
    input_path,
    output_path,
    compiler="g++",
    debug=True,
    sanitize=True,
    edulcni_root=None,
    viewer=None,
    include_dir=None,
    library_dir=None,
    bootstrap="edulcni/bootstrap.hpp",
    extra_compile_flags=None,
    extra_link_flags=None,
):
    paths = _resolve_paths(edulcni_root, viewer, include_dir, library_dir)
    executable = _compile(
        problem=problem,
        compiler=compiler,
        debug=debug,
        sanitize=sanitize,
        include_dir=paths["include_dir"],
        library_dir=paths["library_dir"],
        bootstrap=bootstrap,
        extra_compile_flags=extra_compile_flags or [],
        extra_link_flags=extra_link_flags or [],
    )

    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    token = secrets.token_urlsafe(24)
    viewer_process = _start_viewer(paths["viewer"], token)
    solution_process = None

    try:
        port = _wait_until_ready(viewer_process)
        environment = os.environ.copy()
        environment.update(
            {
                "EDULCNI_HOST": "127.0.0.1",
                "EDULCNI_PORT": str(port),
                "EDULCNI_TOKEN": token,
            }
        )

        with input_path.open("rb") as input_file, output_path.open("wb") as output_file:
            solution_process = subprocess.Popen(
                [str(executable)],
                stdin=input_file,
                stdout=output_file,
                env=environment,
            )
            solution_status = solution_process.wait()

        if solution_status != 0:
            print(
                f"Instrumented solution exited with status {solution_status}; "
                "the viewer will keep the frames received so far.",
                file=sys.stderr,
            )

        viewer_status = viewer_process.wait()
        if viewer_status != 0:
            raise SystemExit(f"Edulcni viewer exited with status {viewer_status}.")
        if solution_status != 0:
            raise SystemExit(solution_status)
    except KeyboardInterrupt:
        if solution_process is not None and solution_process.poll() is None:
            solution_process.terminate()
        if viewer_process.poll() is None:
            viewer_process.terminate()
        raise
    except BaseException:
        if viewer_process.poll() is None:
            viewer_process.terminate()
        raise


def _compile(
    problem,
    compiler,
    debug,
    sanitize,
    include_dir,
    library_dir,
    bootstrap,
    extra_compile_flags,
    extra_link_flags,
):
    source = Path(f"{problem}.cpp")
    if not source.is_file():
        raise SystemExit(f"Source file not found: {source}")

    executable = Path(f"{problem}.edulcni").resolve()
    command = [compiler]
    if sanitize:
        command.extend(SANITIZER_FLAGS)
    command.extend(DEFAULT_COMPILER_FLAGS)
    if debug:
        command.append("-DDEBUG")
    command.extend(
        [
            "-DEDULCNI_ENABLED=1",
            "-include",
            bootstrap,
            f"-I{include_dir}",
        ]
    )
    command.extend(extra_compile_flags)
    command.extend([str(source), "-o", str(executable)])
    command.extend(
        [
            f"-L{library_dir}",
            f"-Wl,-rpath,{library_dir}",
            "-ledulcni",
            "-pthread",
        ]
    )
    command.extend(extra_link_flags)
    subprocess.run(command, check=True)
    return executable


def _start_viewer(viewer, token):
    return subprocess.Popen(
        [
            str(viewer),
            "--listen",
            "127.0.0.1",
            "--port",
            "0",
            "--token",
            token,
        ],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _wait_until_ready(viewer_process, timeout=DEFAULT_READY_TIMEOUT_SECONDS):
    deadline = time.monotonic() + timeout
    while True:
        if viewer_process.poll() is not None:
            raise SystemExit(
                f"Edulcni viewer exited before becoming ready "
                f"(status {viewer_process.returncode})."
            )

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SystemExit("Timed out waiting for the Edulcni viewer to become ready.")

        readable, _, _ = select.select([viewer_process.stdout], [], [], remaining)
        if not readable:
            continue

        line = viewer_process.stdout.readline()
        if not line:
            continue
        line = line.rstrip("\n")
        if line.startswith(READY_PREFIX):
            port_text = line[len(READY_PREFIX):]
            try:
                port = int(port_text)
            except ValueError as error:
                raise SystemExit(f"Invalid Edulcni viewer readiness line: {line}") from error
            if not 1 <= port <= 65535:
                raise SystemExit(f"Invalid Edulcni viewer port: {port}")
            return port
        print(line, file=sys.stderr)


def _resolve_paths(edulcni_root, viewer, include_dir, library_dir):
    root = _resolve_root(edulcni_root)

    include = include_dir or os.environ.get("EDULCNI_INCLUDE_DIR")
    if include is None and root is not None:
        include = root / "include"
    include = _require_directory(include, "Edulcni include directory")

    library = library_dir or os.environ.get("EDULCNI_LIBRARY_DIR")
    if library is None and root is not None:
        candidates = [root / "lib", root / "build" / "lib", root / "build"]
        library = _first_existing_directory_with_library(candidates)
    library = _require_directory(library, "Edulcni library directory")

    viewer_path = viewer or os.environ.get("EDULCNI_VIEWER")
    if viewer_path is None and root is not None:
        candidates = [
            root / "out" / "edulcni-viewer",
            root / "out" / "edulcni_viewer",
            root / "build" / "edulcni-viewer",
            root / "build" / "edulcni_viewer",
            root / "build" / "bin" / "edulcni-viewer",
        ]
        viewer_path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if viewer_path is None:
        viewer_path = shutil.which("edulcni-viewer")
    viewer_path = _require_executable(viewer_path)

    return {
        "root": root,
        "include_dir": include,
        "library_dir": library,
        "viewer": viewer_path,
    }


def _resolve_root(explicit_root):
    configured = explicit_root or os.environ.get("EDULCNI_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"Edulcni root not found: {root}")
        return root

    checkout_candidate = Path(__file__).resolve().parents[2] / "edulcni"
    if checkout_candidate.is_dir():
        return checkout_candidate
    return None


def _first_existing_directory_with_library(candidates):
    library_names = ("libedulcni.a", "libedulcni.so", "libedulcni.dylib")
    for candidate in candidates:
        if candidate.is_dir() and any((candidate / name).is_file() for name in library_names):
            return candidate
    return None


def _require_directory(path, description):
    if path is None:
        raise SystemExit(
            f"{description} was not found. Set EDULCNI_ROOT or pass an explicit path."
        )
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"{description} not found: {resolved}")
    return resolved


def _require_executable(path):
    if path is None:
        raise SystemExit(
            "Edulcni viewer was not found. Set EDULCNI_ROOT, EDULCNI_VIEWER, "
            "or pass --viewer."
        )
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise SystemExit(f"Edulcni viewer is not executable: {resolved}")
    return resolved
