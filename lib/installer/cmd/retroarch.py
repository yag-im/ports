from lib.app_desc import AppDesc
from lib.retroarch.retroarch import (
    RetroArch,
    RetroArchCore,
)

CMD_GEN_RUN_SCRIPT = "gen_run_script"


def exec_subtask(task: dict, retroarch: RetroArch) -> None:
    cmd = list(task.keys())[0]
    task = task[cmd]
    if cmd == CMD_GEN_RUN_SCRIPT:
        core_name = task.get("core")
        core = RetroArchCore(core_name)
        if core is None:
            raise ValueError(f"Unknown RetroArch core: {core_name}")
        file = task.get("file", None)
        retroarch.gen_run_script(core, file)
    else:
        raise ValueError(f"unrecognized command: {cmd}")


def run(task: dict, app_descr: AppDesc) -> None:
    dst_dir = app_descr.dst_path()
    retroarch = RetroArch(root_dir=dst_dir)
    task_: dict
    for task_ in task.get("tasks"):
        exec_subtask(task_, retroarch)
