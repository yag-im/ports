from pathlib import Path

from lib.app_desc import AppDesc
from lib.installer.cmd.copy import run as exec_copy
from lib.installer.cmd.dosbox import run as exec_dosbox
from lib.installer.cmd.extract import run as exec_extract
from lib.installer.cmd.file import run as exec_file
from lib.installer.utils import prepare_tasks

CMD_COPY = "copy"
CMD_DOSBOX = "dosbox"
CMD_EXTRACT = "extract"
CMD_FILE = "file"


class Parser:
    def __init__(self) -> None:
        pass

    def exec_task(self, app_descr: AppDesc, task: dict) -> None:
        cmd = next(iter(task))
        if cmd == CMD_COPY:
            exec_copy(task, app_descr)
        elif cmd == CMD_DOSBOX:
            exec_dosbox(task, app_descr)
        elif cmd == CMD_EXTRACT:
            exec_extract(task)
        elif cmd == CMD_FILE:
            exec_file(task)
        else:
            raise ValueError(f"unknown cmd: {cmd}")

    def run(self, app_descr: AppDesc, installer: dict) -> None:
        Path(app_descr.dst_path()).mkdir(parents=True, exist_ok=True)
        prepare_tasks(app_descr, installer)
        tasks: list[dict] = installer.get("tasks")
        for task in tasks:
            self.exec_task(app_descr, task)
