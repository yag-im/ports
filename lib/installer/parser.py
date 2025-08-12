from pathlib import Path

from lib.app_desc import AppDesc
from lib.installer.cmd.copy import run as exec_copy
from lib.installer.cmd.dosbox import run as exec_dosbox
from lib.installer.cmd.extract import run as exec_extract
from lib.installer.cmd.file import run as exec_file
from lib.installer.cmd.innoextract import run as exec_innoextract
from lib.installer.cmd.move import run as exec_move
from lib.installer.cmd.replace import run as exec_replace
from lib.installer.cmd.retroarch import run as exec_retroarch
from lib.installer.cmd.scummvm import run as exec_scummvm
from lib.installer.cmd.shell import run as exec_shell
from lib.installer.cmd.wine import run as exec_wine
from lib.installer.utils import prepare_tasks

CMD_COPY = "copy"
CMD_DOSBOX = "dosbox"
CMD_EXTRACT = "extract"
CMD_FILE = "file"
CMD_INNOEXTRACT = "innoextract"
CMD_MOVE = "move"
CMD_REPLACE = "replace"
CMD_RETROARCH = "retroarch"
CMD_SCUMMVM = "scummvm"
CMD_SHELL = "shell"
CMD_WINE = "wine"


class Parser:
    def __init__(self) -> None:
        pass

    def exec_task(self, task: dict, app_descr: AppDesc) -> None:
        cmd = list(task.keys())[0]
        task = task[cmd]
        if cmd == CMD_COPY:
            exec_copy(task, app_descr)
        elif cmd == CMD_DOSBOX:
            exec_dosbox(task, app_descr)
        elif cmd == CMD_EXTRACT:
            exec_extract(task, app_descr)
        elif cmd == CMD_FILE:
            exec_file(task)
        elif cmd == CMD_INNOEXTRACT:
            exec_innoextract(task)
        elif cmd == CMD_MOVE:
            exec_move(task)
        elif cmd == CMD_REPLACE:
            exec_replace(task)
        elif cmd == CMD_RETROARCH:
            exec_retroarch(task, app_descr)
        elif cmd == CMD_SCUMMVM:
            exec_scummvm(task, app_descr)
        elif cmd == CMD_SHELL:
            exec_shell(task)
        elif cmd == CMD_WINE:
            exec_wine(task, app_descr)
        else:
            raise ValueError(f"unknown cmd: {cmd}")

    def run(self, app_descr: AppDesc, installer: dict) -> None:
        Path(app_descr.dst_path()).mkdir(parents=True, exist_ok=True)
        prepare_tasks(app_descr, installer)
        tasks: list[dict] = installer.get("tasks")
        for task in tasks:
            self.exec_task(task, app_descr)
