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
    BUNDLES_BASE_DIR,
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
    replace,
)


@dataclass
class DosBoxWin3xConf(DosBoxConf):
    flavor: DosBoxFlavor = field(default=DosBoxFlavor.WIN311)
    mod: DosBoxMod = field(default=DosBoxMod.X)


class DosBoxWin3x(DosBox[DosBoxWin3xConf]):
    def __init__(self, root_dir: Path, app_descr: AppDesc, conf: DosBoxWin3xConf = DosBoxWin3xConf()) -> None:
        super().__init__(root_dir, conf, app_descr)
        # copy bundled system folder: bundles/dosbox-x/win311-en -> root_dir/C
        copy(
            BUNDLES_BASE_DIR / self.conf.mod.value / f"{self.conf.flavor.value}-{self.conf.lang}",
            self.system_drive,
            copy_tree=True,
        )
        self.app_drive.mkdir(exist_ok=False)
        self.conf.mount(
            [
                DosMountPointHDD(SYSTEM_DRIVE_LETTER, self.system_drive),
                DosMountPointHDD(APP_DRIVE_LETTER, self.app_drive),
            ]
        )
        self.set_display_params(self.app_descr.app_reqs.screen_width, self.app_descr.app_reqs.color_bits)

    def set_display_params(self, screen_width: int, color_bits: int):
        system_ini_file_path = self.system_drive / "WINDOWS" / "SYSTEM.INI"
        replace(system_ini_file_path, "screen-size=[0-9]+", f"screen-size={screen_width}")
        replace(system_ini_file_path, "color-format=[0-9]+", f"color-format={color_bits}")

    def run(self, path: PureWindowsPath, args: List[Any] = [], exit=True, mock=False) -> None:
        """Runs existing app in the Win311-flavored env"""

        cmds = []
        if self.conf.lang == "ru":
            cmds.append(DosCmdExec("CHCP", [866]))
        app_exec = [path, *args]
        if exit:
            app_exec.insert(0, "RUNEXIT.EXE")
        cmds.append(DosCmdExec("C:\\WINDOWS\\WIN", app_exec))
        self._run(cmds, mock=mock)
