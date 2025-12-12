from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.installer.utils import transform_str_path
from lib.qemu.qemu import (
    Qemu,
    QemuFlavor,
)
from lib.qemu.qemu_win9x import (
    QemuWin9x,
    QemuWin9xConf,
)
from lib.qemu.qemu_winxp import (
    QemuWinXp,
    QemuWinXpConf,
)

CMD_COPY = "copy"
CMD_GEN_RUN_SCRIPT = "gen_run_script"
CMD_MOUNT = "mount"
CMD_REGEDIT = "regedit"
CMD_RUN = "run"
CMD_UMOUNT = "umount"
CMD_EXTRACT = "extract"


def exec_subtask(task: dict, qemu: Qemu) -> None:
    cmd = list(task.keys())[0]
    task = task[cmd]
    if cmd == CMD_COPY:
        qemu.copy(Path(task.get("src")), Path(task.get("dest")))
    elif cmd == CMD_GEN_RUN_SCRIPT:
        qemu.gen_run_script(exec_path=PureWindowsPath(task.get("path")), do_exit=task.get("exit", True))
    elif cmd == CMD_MOUNT:
        src = Path(task.get("src"))
        cd_images_as_letters = task.get("cd_images_as_letters", False)
        if cd_images_as_letters:
            cur_letter = FIRST_CD_DRIVE_LETTER
            image_path = Path(src / cur_letter)
            while image_path.exists():
                qemu.mount(image_path=image_path, media="cdrom", letter=cur_letter)
                cur_letter = chr(ord(cur_letter) + 1)
                image_path = Path(src / cur_letter)
        else:
            qemu.mount(image_path=src, media="cdrom", letter=task.get("letter"))
    elif cmd == CMD_REGEDIT:
        qemu.upd_reg({task.get("path"): task.get("values")})
    elif cmd == CMD_RUN:
        qemu.run_exec(
            exec_path=PureWindowsPath(task.get("path")), do_exit=task.get("exit", True), args=task.get("args", None)
        )
    elif cmd == CMD_UMOUNT:
        remove = task.get("remove", True)
        qemu.umount(drive_letter=task.get("letter"), remove=remove)
    elif cmd == CMD_EXTRACT:
        src = transform_str_path(task.get("src"))
        dest = transform_str_path(task.get("dest"))
        files = task.get("files", None)
        qemu.extract(src, dest, files)
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def run(task: dict, app_descr: AppDesc) -> None:
    input_conf = task.get("conf", {})
    flavor = QemuFlavor[str(task.get("flavor", "WINXPSP3")).upper()]
    input_conf["flavor"] = flavor
    dst_dir = app_descr.dst_path()
    if flavor == QemuFlavor.WINXPSP3:
        qemu = QemuWinXp(root_dir=dst_dir, app_descr=app_descr, conf=QemuWinXpConf(**input_conf))
    elif flavor == QemuFlavor.WIN98SE:
        qemu = QemuWin9x(root_dir=dst_dir, app_descr=app_descr, conf=QemuWin9xConf(**input_conf))
    else:
        raise ValueError(f"unrecognized flavor: {flavor}")

    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(task_, qemu)
