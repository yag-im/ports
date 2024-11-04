from pathlib import Path

from lib.errors import DistroNotFoundException
from lib.unpack import unpack_disc_image
from lib.utils import rm
from lib.wine.wine import Wine


def unpack_cds_as_letters(src_folder: Path, dst_folder: Path, files: list[str], first_cd_letter: chr) -> None:
    """Unpack CD images into letter folders, e.g.:

    {src_folder}/1.iso -> {dst_folder}/E
    {src_folder}/2.iso -> {dst_folder}/F
    """
    cd_letter = first_cd_letter
    for f in files:
        src_path = src_folder / f
        if not src_path.exists():
            raise DistroNotFoundException(src_path)
        unpack_disc_image(src_path, dst_folder / cd_letter)
        cd_letter = chr(ord(cd_letter) + 1)


def unmount_cds(wine: Wine, dst_folder: Path, first_cd_letter: chr, num: int, remove: bool = True):
    cd_letter = first_cd_letter
    for _ in range(num):
        if remove:
            wine.remove_drive(cd_letter)
            rm(dst_folder / cd_letter)
        cd_letter = chr(ord(cd_letter) + 1)
