from lib.app_desc import AppDesc
from lib.installer.cmd.dosbox import CMD_GEN_RUN_SCRIPT
from lib.retroarch.retroarch import RetroArch


def exec_subtask(task: dict, retroarch: RetroArch) -> None:
    cmd = list(task.keys())[0]
    task = task[cmd]
    if cmd == CMD_GEN_RUN_SCRIPT:
        core = task.get("core")
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
