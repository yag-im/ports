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
    Union,
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
from lib.utils import copy

XCOPY_CMD = "XCOPY"
XCOPY_CMD_OPTIONS = ["/I", "/E", "/Y", "/H", "/R"]
MAX_DOS_MEMORY = 16


@dataclass
class DosBoxDosConf(DosBoxConf):
    flavor: DosBoxFlavor = field(default=DosBoxFlavor.DOS)
    mod: DosBoxMod = field(default=DosBoxMod.ORIG)
    memsize: int = MAX_DOS_MEMORY


class DosBoxDos(DosBox[DosBoxConf]):
    def __init__(self, root_dir: Path, app_descr: AppDesc, conf: DosBoxConf = DosBoxDosConf()) -> None:
        super().__init__(root_dir, conf, app_descr)
        self.system_drive.mkdir(exist_ok=False)
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

    def copy(self, src: Union[Path, List[Path], PureWindowsPath, List[PureWindowsPath]], dst: PureWindowsPath) -> None:
        if not isinstance(src, List):
            src = [src]
        cmds = []
        for s in src:
            cmds.append(DosCmdExec(XCOPY_CMD, [s, dst, *XCOPY_CMD_OPTIONS]))
        self._run(cmds)

    def run(self, path: PureWindowsPath, args: List[Any] = None, mock=False) -> None:
        if args is None:
            args = []
        cmds = []
        if self.conf.lang == "ru":
            cmds.append(DosCmdExec("CHCP", [866]))
        cmds.append(DosCmdExec(path, args))
        self._run(cmds, mock=mock)
