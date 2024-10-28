from pathlib import Path

from lib.dosbox.dosbox import (
    DosBox,
    DosMountPoint,
)
from lib.dosbox.misc import DosMountPointCD
from lib.errors import DistroNotFoundException
from lib.utils import (
    copy,
    rm,
)


def copy_distro_files_as_cd_letters(src_folder: Path, dst_folder: Path, files: list[str], first_cd_letter: chr) -> None:
    """Copy distro files as CDs, e.g.:

    {src_folder}/1.iso -> {dst_folder}/E
    {src_folder}/2.iso -> {dst_folder}/F
    """
    cd_letter = first_cd_letter
    for f in files:
        src_path = src_folder / f
        if not src_path.exists():
            raise DistroNotFoundException(src_path)
        copy(src_path, dst_folder / cd_letter)
        cd_letter = chr(ord(cd_letter) + 1)


def gen_cd_mount_points(src_folder: Path, first_cd_letter: str, num: int) -> list[DosMountPoint]:
    """Generate common mount points for CDs, e.g.:

    E: {src_folder}/E
    F: {src_folder}/F
    """
    res = []
    cd_letter = first_cd_letter
    for _ in range(num):
        res.append(DosMountPointCD(letter=cd_letter, path=src_folder / cd_letter))
        cd_letter = chr(ord(cd_letter) + 1)
    return res


def unmount_remove_mounted_cd(dbox: DosBox, dst_folder: Path, cd_letter: chr):
    dbox.umount(cd_letter)
    rm(dst_folder / cd_letter)


def unmount_remove_mounted_cds(dbox: DosBox, dst_folder: Path, first_cd_letter: chr, num: int):
    cd_letter = first_cd_letter
    for _ in range(num):
        unmount_remove_mounted_cd(dbox, dst_folder, cd_letter)
        cd_letter = chr(ord(cd_letter) + 1)
