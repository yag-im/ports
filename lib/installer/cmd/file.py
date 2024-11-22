from pathlib import Path

from lib.utils import rm


def get_default_state(task: dict) -> str:
    # Default is the current state of the file if it exists, directory if recurse=yes, or file otherwise.
    path = Path(task.get("path"))
    default_state = "file"
    if path.exists():
        if path.is_dir():
            default_state = "directory"
        elif path.is_symlink():
            default_state = "link"
    else:
        recurse = task.get("recurse", False)
        if recurse:
            default_state = "directory"
    return default_state


def run(task: dict) -> None:
    path = Path(task.get("path"))
    exists = path.exists()
    state = task.get("state", get_default_state(task))
    if state == "directory":
        if exists:
            return
        path.mkdir(parents=True)
    elif state == "absent":
        rm(path)
