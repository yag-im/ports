from pathlib import Path

from lib.app_desc import AppDesc
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.installer.utils import unpack_cd_images_as_letters
from lib.unpack import (
    unpack_archive,
    unpack_disc_image,
)


def run(task: dict, app_descr: AppDesc) -> None:
    src = Path(task.get("src"))
    files = task.get("files")
    dest = Path(task.get("dest"))
    cd_images_as_letters = task.get("cd_images_as_letters", False)
    if cd_images_as_letters:
        unpack_cd_images_as_letters(
            src_dir=src,
            dst_dir=dest,
            files=task.get("files", app_descr.distro.files),
            first_cd_letter=task.get("first_cd_drive_letter", FIRST_CD_DRIVE_LETTER),
        )
    else:
        if "cd" in app_descr.distro.format.lower():
            # src.suffix.lower()[1:] in ["iso", "nrg", "mdf", "pdi", "cdi", "bin", "cue", "b5i", "img"]:
            # FD images can also have img extensions, so switch by distro format
            unpack_disc_image(src, dest, files)
        else:
            unpack_archive(src, dest, files)
