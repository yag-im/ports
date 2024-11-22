from pathlib import Path

from lib.utils import move


def run(task: dict) -> None:
    src = Path(task.get("src"))
    # do not add support for multi-sources here; use loop/item in the playbook instead
    dest = Path(task.get("dest"))
    copy_tree = task.get("copy_tree", False)
    move(src, dest, copy_tree=copy_tree)
