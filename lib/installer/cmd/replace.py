from pathlib import Path

from lib.utils import replace


def run(task: dict) -> None:
    path = Path(task.get("path"))
    regexp = task.get("regexp")
    repl = task.get("replace")
    replace(path, regexp, repl)
