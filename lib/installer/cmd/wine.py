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
CMD_WINETRICKS = "winetricks"
CMD_MSIEXEC = "msiexec"


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
        # VirtualDesktop will not be used only when it's explicitly set to False;
        # if it's empty or explicitly set - it will be used.
        virtual_desktop = task.get("virtual_desktop", None)
        if virtual_desktop:
            virtual_desktop = VirtualDesktopResolution(virtual_desktop)
        elif virtual_desktop is False:
            virtual_desktop = None
        else:
            virtual_desktop = VirtualDesktopResolution.RES_640_480
        wine.run(
            path=task.get("path"),
            args=task.get("args", None),
            virtual_desktop=virtual_desktop,
        )
    elif cmd == CMD_GEN_RUN_SCRIPT:
        path = PureWindowsPath(task.get("path"))
        chdir = task.get("chdir", True)
        wine.gen_run_script(app_exec=path.name, work_dir=path.parent, chdir=chdir)
    elif cmd == CMD_WINETRICKS:
        cmd_ = task.get("cmd")
        quiet = task.get("quiet", False)
        wine.run_winetricks(cmd_, quiet=quiet)
    elif cmd == CMD_MSIEXEC:
        wine.msiexec(task.get("path"))
    elif cmd == CMD_UMOUNT:
        wine.remove_drive(task.get("letter"), task.get("remove", True))
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
