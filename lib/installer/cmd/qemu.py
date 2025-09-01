from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.qemu.qemu import (
    Qemu,
    QemuConf,
    QemuFlavor,
)

CMD_COPY = "copy"
CMD_GEN_RUN_SCRIPT = "gen_run_script"
CMD_MOUNT = "mount"
CMD_REGEDIT = "regedit"
CMD_RUN = "run"
CMD_UMOUNT = "umount"


def exec_subtask(task: dict, qemu: Qemu) -> None:
    cmd = list(task.keys())[0]
    task = task[cmd]
    if cmd == CMD_COPY:
        qemu.copy(task.get("src"), task.get("dest"))
    elif cmd == CMD_GEN_RUN_SCRIPT:
        qemu.gen_run_script(PureWindowsPath(task.get("path")))
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
        qemu.run_exec(PureWindowsPath(task.get("path")))
    elif cmd == CMD_UMOUNT:
        pass
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def run(task: dict, app_descr: AppDesc) -> None:
    qemu_conf = task.get("conf", {})
    flavor = QemuFlavor[str(task.get("flavor", "WINXPSP3")).upper()]
    qemu_conf["flavor"] = flavor
    dst_dir = app_descr.dst_path()
    qemu = Qemu(root_dir=dst_dir, app_descr=app_descr, conf=QemuConf(**qemu_conf))
    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(task_, qemu)
