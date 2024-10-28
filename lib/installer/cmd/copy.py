from pathlib import Path

from lib.app_desc import AppDesc
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.installer.utils import copy_cd_images_as_letters
from lib.utils import copy


def exec(task: dict, app_descr: AppDesc) -> None:
    src = Path(task.get("src"))
    dest = Path(task.get("dest"))
    cd_images_as_letters = task.get("cd_images_as_letters", False)
    if cd_images_as_letters:
        copy_cd_images_as_letters(
            src_dir=src,
            dst_dir=dest,
            files=task.get("files", app_descr.distro.files),
            first_cd_letter=task.get("first_cd_drive_letter", FIRST_CD_DRIVE_LETTER),
        )
    else:
        copy_tree = task.get("copy_tree", False)
        copy(src, dest, copy_tree)
