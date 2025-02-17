import subprocess


def run(task: dict) -> None:
    cmd = task.get("cmd")
    subprocess.run(cmd, shell=True, check=True)
