from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.wine.wine import (
    VirtualDesktopResolution,
    Wine,
)

CMD_GEN_RUN_SCRIPT = "gen_run_script"
CMD_MOUNT = "mount"
CMD_RUN = "run"
CMD_UMOUNT = "umount"


def exec_run(wine: Wine, task: dict):
    wine.run(
        path=task.get("path"),
        args=task.get("args", None),
        virtual_desktop=VirtualDesktopResolution.RES_640_480,
    )


def exec_subtask(wine: Wine, task: dict) -> None:
    cmd = next(iter(task))
    if cmd == CMD_MOUNT:
        wine.add_cdrom(
            letter=task.get("letter"),
            target=Path(task.get("src")),
            replace=task.get("replace", True),
            label=task.get("label", None),
        )
    elif cmd == CMD_RUN:
        exec_run(wine, task)
    elif cmd == CMD_GEN_RUN_SCRIPT:
        path = PureWindowsPath(task.get("path"))
        wine.gen_run_script(app_exec=path.name, work_dir=path.parent)
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def run(task: dict, app_descr: AppDesc) -> None:
    dst_dir = app_descr.dst_path()
    wine = Wine(dst_dir)
    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(wine, task_)
