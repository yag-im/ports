from pathlib import Path

from lib.app_desc import AppDesc
from lib.installer.cmd.dosbox import CMD_GEN_RUN_SCRIPT
from lib.scummvm.scummvm import (
    ScummVm,
    ScummVmConf,
)


def exec_subtask(scummvm: ScummVm, task: dict, app_descr: AppDesc) -> None:
    cmd = next(iter(task))
    if cmd == CMD_GEN_RUN_SCRIPT:
        game = task.get("game")
        lang = task.get("lang", app_descr.lang)
        path = task.get("path", None)
        path = Path(path) if path else None
        scummvm.gen_run_script(game, lang, app_dir=path)
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def run(task: dict, app_descr: AppDesc) -> None:
    dst_dir = app_descr.dst_path()
    filtering = task.get("filtering", True)
    fullscreen = task.get("fullscreen", True)
    subtitles = task.get("subtitles", True)
    scummvm = ScummVm(
        root_dir=dst_dir, conf=ScummVmConf(filtering=filtering, fullscreen=fullscreen, subtitles=subtitles)
    )
    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(scummvm, task_, app_descr)
