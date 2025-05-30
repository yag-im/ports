from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.wine.wine import (
    OsVer,
    VirtualDesktopResolution,
    Wine,
)

CMD_GEN_RUN_SCRIPT = "gen_run_script"
CMD_MOUNT = "mount"
CMD_REGEDIT = "regedit"
CMD_RUN = "run"
CMD_UMOUNT = "umount"


def exec_run(wine: Wine, task: dict):
    wine.run(
        path=task.get("path"),
        args=task.get("args", None),
        virtual_desktop=VirtualDesktopResolution.RES_640_480,
    )


def exec_subtask(task: dict, wine: Wine) -> None:
    cmd = list(task.keys())[0]
    task = task[cmd]
    if cmd == CMD_MOUNT:
        wine.add_cdrom(
            letter=task.get("letter"),
            target=Path(task.get("src")),
            replace=task.get("replace", True),
            label=task.get("label", None),
        )
    elif cmd == CMD_REGEDIT:
        wine.upd_reg({task.get("path"): task.get("values")})
    elif cmd == CMD_RUN:
        exec_run(wine, task)
    elif cmd == CMD_GEN_RUN_SCRIPT:
        path = PureWindowsPath(task.get("path"))
        chdir = task.get("chdir", True)
        wine.gen_run_script(app_exec=path.name, work_dir=path.parent, chdir=chdir)
    elif cmd == "winetricks":
        cmd_ = task.get("cmd")
        quiet = task.get("quiet", False)
        wine.run_winetricks(cmd_, quiet=quiet)
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def run(task: dict, app_descr: AppDesc) -> None:
    dst_dir = app_descr.dst_path()
    os_ver = task.get("os_ver", OsVer.WINDOWS7.value)
    virtual_desktop = task.get("virtual_desktop", None)
    if virtual_desktop:
        virtual_desktop = VirtualDesktopResolution(virtual_desktop)
    wine = Wine(
        dst_dir,
        os_ver=OsVer(os_ver),
        lang=app_descr.lang,
        virtual_desktop=virtual_desktop,
    )
    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(task_, wine)
