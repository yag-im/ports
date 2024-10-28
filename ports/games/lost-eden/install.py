import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
)
from lib.dosbox.dosbox_dos import (
    DosBoxDos,
    DosBoxDosConf,
)
from lib.dosbox.misc import DosMountPoint
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.utils import copy

CURRENT_DIR = Path(__file__).resolve().parent

APP_EXEC_PATH = APP_DIR / "EDEN.BAT"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            # TODO: fix cracky sound
            copy(src_folder / app_desc.distro.files[0], dst_folder / FIRST_CD_LETTER)
            dbox = DosBoxDos(dst_folder, app_desc, conf=DosBoxDosConf(cycles="max"))
            dbox.mount(DosMountPoint(FIRST_CD_LETTER, dst_folder / FIRST_CD_LETTER, is_cd=True))
            dbox.run(FIRST_CD_DRIVE_DIR / "INSTALL.EXE")
            copy(CURRENT_DIR / "files" / "EDEN.BAT", dst_folder / APP_DRIVE_LETTER / "APP")
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
