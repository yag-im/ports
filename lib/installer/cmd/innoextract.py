from pathlib import Path

from lib.unpack import unpack_innoextract


def run(task: dict) -> None:
    src = Path(task.get("src"))
    dest = Path(task.get("dest"))
    files = task.get("files")
    gog = task.get("gog", False)
    unpack_innoextract(src, dest, is_gog=gog, files=files)
