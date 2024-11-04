from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
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
from lib.dosbox.misc import DosMountPoint
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.installer.utils import transform_str_path

CMD_COPY = "copy"
CMD_GEN_RUN_SCRIPT = "gen_run_script"
CMD_MOUNT = "mount"
CMD_RUN = "run"
CMD_UMOUNT = "umount"


def exec_run(dbox: DosBox, task: dict, mock=False):
    if isinstance(dbox, DosBoxDos):
        dbox.run(path=PureWindowsPath(task.get("path")), args=task.get("args", []), mock=mock)
    elif isinstance(dbox, DosBoxWin3x):
        dbox.run(
            path=PureWindowsPath(task.get("path")), args=task.get("args", []), runexit=task.get("exit", True), mock=mock
        )
    elif isinstance(dbox, DosBoxWin9x):
        dbox.run(
            path=PureWindowsPath(task.get("path")),
            args=task.get("args", []),
            runexit=task.get("exit", True),
            mock=mock,
            umount_x=task.get("unmount_x", True),
        )
    else:
        raise ValueError(f"unrecognized dbox: {dbox}")


def exec_subtask(app_descr: AppDesc, dbox: DosBox, task: dict) -> None:
    cmd = next(iter(task))
    if cmd == CMD_COPY:
        src = task.get("src")
        if isinstance(src, str):
            src = [src]
        transformed_srcs = []
        for src_ in src:
            transformed_srcs.append(transform_str_path(src_))
        dbox.copy(transformed_srcs, transform_str_path(task.get("dest")))
    elif cmd == CMD_GEN_RUN_SCRIPT:
        exec_run(dbox, task, mock=True)
    elif cmd == CMD_MOUNT:
        cd_images_as_letters = task.get("cd_images_as_letters", False)
        if cd_images_as_letters:
            dbox.mount(gen_cd_mount_points(Path(task.get("src")), FIRST_CD_DRIVE_LETTER, len(app_descr.distro.files)))
        else:
            dbox.mount(
                DosMountPoint(
                    letter=task.get("letter"),
                    path=Path(task.get("src")),
                    is_cd=task.get("is_cd", True),
                    label=task.get("label", None),
                )
            )
    elif cmd == CMD_RUN:
        exec_run(dbox, task)
    elif cmd == CMD_UMOUNT:
        cd_images_as_letters = task.get("cd_images_as_letters", False)
        remove = task.get("remove", True)
        if cd_images_as_letters:
            dbox.umount_all(remove, cd_only=True)
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def run(task: dict, app_descr: AppDesc) -> None:
    dosbox_conf = task.get("conf", {})
    flavor = DosBoxFlavor[str(task.get("flavor")).upper()]
    dosbox_conf["flavor"] = flavor
    mod = task.get("mod", None)
    if mod:
        mod = DosBoxMod[str(mod).upper()]
        dosbox_conf["mod"] = mod
    dst_dir = app_descr.dst_path()
    if flavor == DosBoxFlavor.WIN311:
        dbox = DosBoxWin3x(root_dir=dst_dir, app_descr=app_descr, conf=DosBoxWin3xConf(**dosbox_conf))
    elif flavor in {DosBoxFlavor.WIN95OSR21, DosBoxFlavor.WIN95OSR25, DosBoxFlavor.WIN98SE}:
        dbox = DosBoxWin9x(root_dir=dst_dir, app_descr=app_descr, conf=DosBoxWin9xConf(**dosbox_conf))
    elif flavor == DosBoxFlavor.DOS:
        dbox = DosBoxDos(root_dir=dst_dir, app_descr=app_descr, conf=DosBoxDosConf(**dosbox_conf))
    else:
        raise ValueError(f"unrecognized flavor {flavor}")
    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(app_descr, dbox, task_)
