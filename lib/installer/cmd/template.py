from pathlib import Path

from lib.utils import template


def run(task: dict) -> None:
    src = Path(task.get("src"))
    dest = Path(task.get("dest"))
    params = task.get("params", {})
    newline = task.get("newline", None)
    template(src, dest, params, newline)
