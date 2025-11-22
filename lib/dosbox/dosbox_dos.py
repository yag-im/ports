from dataclasses import (
    dataclass,
    field,
)
from pathlib import (
    Path,
    PureWindowsPath,
)
from typing import (
    Any,
    List,
)

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DRIVE_LETTER,
    RUNNERS_BUNDLES_BASE_DIR,
    SYSTEM_DRIVE_LETTER,
)
from lib.dosbox.dosbox import DosBox
from lib.dosbox.dosbox_conf import (
    DosBoxConf,
    DosBoxFlavor,
    DosBoxMod,
)
from lib.dosbox.misc import (
    DosCmdExec,
    DosMountPointHDD,
)
from lib.utils import (
    copy,
)

MAX_DOS_MEMORY = 16


@dataclass
class DosBoxDosConf(DosBoxConf):
    flavor: DosBoxFlavor = field(default=DosBoxFlavor.DOS)
    mod: DosBoxMod = field(default=DosBoxMod.ORIG)
    memsize: int = MAX_DOS_MEMORY


class DosBoxDos(DosBox[DosBoxConf]):
    def __init__(self, root_dir: Path, app_descr: AppDesc, conf: DosBoxConf = DosBoxDosConf()) -> None:
        super().__init__(root_dir, conf, app_descr)
        self.system_drive.mkdir(exist_ok=True)
        copy(
            RUNNERS_BUNDLES_BASE_DIR / self.conf.mod.value / "dos",
            self.system_drive,
            copy_tree=True,
        )
        self.app_drive.mkdir(exist_ok=True)
        self.conf.mount(
            [
                DosMountPointHDD(SYSTEM_DRIVE_LETTER, self.system_drive),
                DosMountPointHDD(APP_DRIVE_LETTER, self.app_drive),
            ]
        )
        if conf.gus:
            copy(
                RUNNERS_BUNDLES_BASE_DIR / self.conf.mod.value / "ULTRASND",
                self.system_drive,
            )

    def run(self, path: PureWindowsPath, args: List[Any] = None, mock=False, cd=None, pre_exec=None) -> None:
        if args is None:
            args = []
        cmds = []
        if self.conf.lang == "ru":
            cmds.append(DosCmdExec("CHCP", [866]))
        if pre_exec:
            for cmd in pre_exec:
                cmds.append(cmd)
        cmds.append(DosCmdExec(path, args, cd))
        self._run(cmds, mock=mock)
