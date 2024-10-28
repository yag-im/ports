from pathlib import Path
from shutil import unpack_archive

from lib.unpack import unpack_disc_image


def exec(task: dict) -> None:
    src = Path(task.get("src"))
    files = task.get("files")
    dest = Path(task.get("dest"))
    copy_tree = task.get("copy_tree", False)
    if src.suffix.lower()[1:] in ["iso", "nrg", "mdf", "pdi", "cdi", "bin", "cue", "b5i", "img"]:
        unpack_disc_image(src, dest, files, copy_tree=copy_tree)
    else:
        unpack_archive(src, dest, files, copy_tree=copy_tree)
