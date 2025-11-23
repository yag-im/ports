from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.dosbox.const import DEFAULT_APP_DRIVE_SIZE
from lib.dosbox.dosbox import DosBox
from lib.dosbox.dosbox_conf import (
    DosBoxFlavor,
    DosBoxMod,
)
from lib.dosbox.dosbox_dos import (
    DosBoxDos,
    DosBoxDosConf,
)
from lib.dosbox.dosbox_win3x import (
    DosBoxWin3x,
    DosBoxWin3xConf,
)
from lib.dosbox.dosbox_win9x import (
    DosBoxWin9x,
    DosBoxWin9xConf,
)
from lib.dosbox.helpers import gen_cd_mount_points
from lib.dosbox.misc import (
    DosMountPoint,
    DosMountPointType,
)
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.installer.utils import transform_str_path

CMD_COPY = "copy"
CMD_GEN_RUN_SCRIPT = "gen_run_script"
CMD_MD = "md"
CMD_MOUNT = "mount"
CMD_REGEDIT = "regedit"
CMD_RUN = "run"
CMD_UMOUNT = "umount"
CMD_EXTRACT = "extract"


def exec_regedit(dbox: DosBoxWin9x, task: dict):
    key_path = task.get("path")
    values = task.get("values")
    dbox.regedit({key_path: values})


def exec_run(dbox: DosBox, task: dict, mock=False):
    run_path = task.get("path")
    if run_path is None:
        raise ValueError("CMD_RUN: missing required field: 'path'")
    if isinstance(dbox, DosBoxDos):
        cd = task.get("cd", None)
        pre_exec = task.get("pre_exec", None)
        if cd:
            cd = PureWindowsPath(cd)
        dbox.run(path=PureWindowsPath(run_path), args=task.get("args", []), cd=cd, mock=mock, pre_exec=pre_exec)
    elif isinstance(dbox, DosBoxWin3x):
        dbox.run(path=PureWindowsPath(run_path), args=task.get("args", []), runexit=task.get("exit", True), mock=mock)
    elif isinstance(dbox, DosBoxWin9x):
        workdir = task.get("workdir", None)
        dbox.run(
            path=PureWindowsPath(run_path),
            args=task.get("args", []),
            runexit=task.get("exit", True),
            mock=mock,
            umount_x=task.get("unmount_x", True),
            workdir=workdir,
        )
    else:
        raise ValueError(f"unrecognized dbox: {dbox}")


def exec_subtask(task: dict, app_descr: AppDesc, dbox: DosBox) -> None:
    cmd = list(task.keys())[0]
    task = task[cmd]
    if cmd == CMD_COPY:
        src = task.get("src")
        if isinstance(src, str):
            # using an array of sources is preferred for copying, as it runs DOSBox once,
            # whereas using a "loop" causes DOSBox to run multiple times.
            src = [src]
        transformed_srcs = []
        for src_ in src:
            transformed_srcs.append(transform_str_path(src_))
        dbox.copy(transformed_srcs, transform_str_path(task.get("dest")))
    elif cmd == CMD_GEN_RUN_SCRIPT:
        exec_run(dbox, task, mock=True)
    elif cmd == CMD_MD:
        dbox.md(PureWindowsPath(task.get("path")))
    elif cmd == CMD_MOUNT:
        cd_images_as_letters = task.get("cd_images_as_letters", False)
        if cd_images_as_letters:
            dbox.mount(gen_cd_mount_points(Path(task.get("src")), FIRST_CD_DRIVE_LETTER, len(app_descr.distro.files)))
        else:
            path = task.get("src")
            if isinstance(path, str):
                path = [Path(path)]
            elif isinstance(path, list):
                path = [Path(p) for p in path]
            else:
                raise ValueError(f"unknown src type: {path}")
            dbox.mount(
                DosMountPoint(
                    letter=task.get("letter"),
                    path=path,
                    type=DosMountPointType[str(task.get("type", "CDROM")).upper()],
                    label=task.get("label", None),
                )
            )
    elif cmd == CMD_REGEDIT:
        exec_regedit(dbox, task)
    elif cmd == CMD_RUN:
        exec_run(dbox, task)
    elif cmd == CMD_UMOUNT:
        cd_images_as_letters = task.get("cd_images_as_letters", False)
        remove = task.get("remove", True)
        if cd_images_as_letters:
            dbox.umount_all(remove, cd_only=True)
        else:
            letter = task.get("letter")
            dbox.umount(letter, remove)
    elif cmd == CMD_EXTRACT:
        src = transform_str_path(task.get("src"))
        dest = transform_str_path(task.get("dest"))
        files = task.get("files", None)
        dbox.extract(src, dest, files)
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def get_dosbox_mod(app_descr: AppDesc) -> DosBoxMod:
    if app_descr.runner.name == "dosbox-x":
        return DosBoxMod.X
    elif app_descr.runner.name == "dosbox-staging":
        return DosBoxMod.STAGE
    elif app_descr.runner.name == "dosbox":
        return DosBoxMod.ORIG


def run(task: dict, app_descr: AppDesc) -> None:
    dosbox_conf = task.get("conf", {})
    flavor = DosBoxFlavor[str(task.get("flavor", "DOS")).upper()]
    dosbox_conf["flavor"] = flavor
    dosbox_conf["mod"] = get_dosbox_mod(app_descr)
    dst_dir = app_descr.dst_path()
    if flavor == DosBoxFlavor.WIN311:
        dbox = DosBoxWin3x(root_dir=dst_dir, app_descr=app_descr, conf=DosBoxWin3xConf(**dosbox_conf))
    elif flavor in {DosBoxFlavor.WIN95OSR21, DosBoxFlavor.WIN95OSR25, DosBoxFlavor.WIN98SE}:
        dosbox_conf["app_drive_size"] = task.get("app_drive_size", DEFAULT_APP_DRIVE_SIZE)
        dbox = DosBoxWin9x(root_dir=dst_dir, app_descr=app_descr, conf=DosBoxWin9xConf(**dosbox_conf))
    elif flavor == DosBoxFlavor.DOS:
        dbox = DosBoxDos(root_dir=dst_dir, app_descr=app_descr, conf=DosBoxDosConf(**dosbox_conf))
    else:
        raise ValueError(f"unrecognized flavor {flavor}")
    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(task_, app_descr, dbox)
