from pathlib import Path

from lib.app_desc import AppDesc
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.installer.utils import unpack_cd_images_as_letters
from lib.unpack import (
    unpack_archive,
    unpack_disc_image,
)

HINT_FLOPPY = "floppy"


def run(task: dict, app_descr: AppDesc) -> None:
    src = Path(task.get("src"))
    files = task.get("files")
    dest = Path(task.get("dest"))
    cd_images_as_letters = task.get("cd_images_as_letters", False)
    hint = task.get("hint", None)
    if cd_images_as_letters:
        unpack_cd_images_as_letters(
            src_dir=src,
            dst_dir=dest,
            files=task.get("files", app_descr.distro.files),
            first_cd_letter=task.get("first_cd_drive_letter", FIRST_CD_DRIVE_LETTER),
        )
    else:
        if hint == HINT_FLOPPY:
            # floppy images can have "img" extensions (like CDs), so using a hint here
            unpack_archive(src, dest, files)
        elif src.suffix.lower()[1:] in ["iso", "nrg", "mdf", "pdi", "cdi", "bin", "cue", "b5i", "img"]:
            unpack_disc_image(src, dest, files)
        else:
            unpack_archive(src, dest, files)
