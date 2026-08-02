from pathlib import (
    Path,
    PureWindowsPath,
)

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


def _to_short_name(name: str) -> str:
    """Convert a single Windows filename/dirname to its 8.3 short-filename form
    when it contains spaces (or otherwise doesn't fit 8.3).

    Example: 'TKKG 8.EXE' -> 'TKKG8~1.EXE', 'PROGRAM FILES' -> 'PROGRA~1'.
    """
    if "." in name:
        base, ext = name.rsplit(".", 1)
    else:
        base, ext = name, ""

    if " " not in name and len(base) <= 8 and len(ext) <= 3:
        return name

    base_clean = base.replace(" ", "").upper()
    ext_clean = ext.replace(" ", "").upper()[:3]
    short_base = base_clean[:6] + "~1"
    if ext_clean:
        return f"{short_base}.{ext_clean}"
    return short_base


def to_short_path(path: str) -> str:
    """Convert a Windows path so that any component containing spaces is replaced
    by its 8.3 short-filename equivalent.

    Example: 'D:\\APP\\TKKG 8.EXE' -> 'D:\\APP\\TKKG8~1.EXE'.
    Path components without spaces are left unchanged.
    """
    if " " not in path:
        return path
    p = PureWindowsPath(path)
    new_parts = []
    for idx, part in enumerate(p.parts):
        # Preserve drive/root parts (e.g. 'D:\\', '\\') as-is
        if idx == 0 and (part.endswith(":\\") or part.endswith(":") or part == "\\"):
            new_parts.append(part)
        elif " " in part:
            new_parts.append(_to_short_name(part))
        else:
            new_parts.append(part)
    return str(PureWindowsPath(*new_parts))


def copy_distro_files_as_cd_letters(src_folder: Path, dst_folder: Path, files: list[str], first_cd_letter: str) -> None:
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


def unmount_remove_mounted_cd(dbox: DosBox, dst_folder: Path, cd_letter: str):
    dbox.umount(cd_letter)
    rm(dst_folder / cd_letter)


def unmount_remove_mounted_cds(dbox: DosBox, dst_folder: Path, first_cd_letter: str, num: int):
    cd_letter = first_cd_letter
    for _ in range(num):
        unmount_remove_mounted_cd(dbox, dst_folder, cd_letter)
        cd_letter = chr(ord(cd_letter) + 1)
