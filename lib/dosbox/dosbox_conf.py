import collections
from dataclasses import (
    dataclass,
    field,
)
from enum import StrEnum
from pathlib import Path
from typing import (
    List,
    Union,
)

from lib.dosbox.misc import DosMountPoint
from lib.utils import rm

BASE_LANG = "en"
BASE_MEMORY_SIZE = 128
BASE_MOUSE_SENSITIVITY = 100


# https://www.dosbox.com/wiki/Dosbox.conf
# https://github.com/dosbox-staging/dosbox-staging/wiki/Config-file-examples#global-config-file
# https://github.com/joncampbell123/dosbox-x/blob/master/dosbox-x.reference.full.conf
class DosBoxMod(StrEnum):
    ORIG = "dosbox"
    STAGE = "dosbox-staging"
    X = "dosbox-x"


class DosBoxFlavor(StrEnum):
    DOS = "dos"
    WIN311 = "win311"
    WIN95OSR21 = "win95osr21"
    WIN95OSR25 = "win95osr25"
    WIN98SE = "win98se"


@dataclass
class DosBoxConf:
    aspect: bool = True
    autolock: bool = False
    cycles: str = "max"
    flavor: DosBoxFlavor = DosBoxFlavor.DOS
    fullscreen: bool = False
    _lang = BASE_LANG
    lock_pointer: bool = False
    memsize: int = BASE_MEMORY_SIZE
    mod: DosBoxMod = DosBoxMod.ORIG
    mount_points: collections.OrderedDict[str, DosMountPoint] = field(default_factory=collections.OrderedDict)
    scaler: str = "none"
    sensitivity: int = BASE_MOUSE_SENSITIVITY

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, new_value):
        # only BASE_LANG and ru DOS versions are supported
        self._lang = new_value if new_value in {BASE_LANG, "ru"} else BASE_LANG

    def mount(
        self,
        mount_points: Union[DosMountPoint, List[DosMountPoint]] = [],
    ) -> None:
        """Adds mounted image/folder"""
        if not isinstance(mount_points, List):
            mount_points = [mount_points]
        for p in mount_points:
            if not p.path.exists():
                raise Exception(f"non-existing mount point: {p.path}")
            self.mount_points[p.letter] = p

    def umount_all(self, remove: bool = False, cd_only: bool = False) -> None:
        mp_copy = self.mount_points.copy()
        for letter, mp in mp_copy.items():
            if cd_only and not mp.is_cd:
                continue
            self.umount(letter, remove)

    def umount(self, drive_letter: str, remove: bool = False) -> None:
        mp = self.mount_points[drive_letter]
        del self.mount_points[drive_letter]
        if remove:
            rm(mp.path)

    def gen_mount_cmds(self, base_dir: Path) -> list[str]:
        """Generate dosbox mount commands.

        Mount point can be:
            - Folder
            - Folder - copy of CD (using -t cdrom -label)
            - CD image (using -t iso)
            - HDD image
        """
        cmds = []
        # mounts should go in alphabetic order, e.g. MOUNT C should go first, then MOUNT D etc.
        for _, m in self.mount_points.items():
            if m.path.is_dir():
                mount_part = f'MOUNT {m.letter} "{m.relative_to(base_dir).path_str()}"'
                if m.is_cd:
                    mount_part += f" -t cdrom -label {m.label}"
                cmds += [mount_part]
            else:
                mount_part = f'IMGMOUNT {m.letter} "{m.relative_to(base_dir).path_str()}"'
                if m.is_cd:
                    mount_part += " -t iso"
                cmds += [mount_part]
        return cmds
