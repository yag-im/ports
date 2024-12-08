import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE,
    FIRST_CD_DRIVE_LETTER,
)
from lib.dosbox.dosbox_conf import DosBoxMod
from lib.dosbox.dosbox_dos import (
    DosBoxDos,
    DosBoxDosConf,
)
from lib.dosbox.misc import DosMountPointCD
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.utils import copy

CURRENT_DIR = Path(__file__).resolve().parent

APP_EXEC_PATH = APP_DIR / "TEENAGNT.EXE"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE / "INSTALUJ.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        app_folder = dst_folder / APP_DRIVE_LETTER / "APP"
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            # we need both BIN and CUE files for CD music to play
            # CUE file should be mounter for CD music
            for img_file in app_desc.distro.files:
                src_path = src_folder / img_file
                if not src_path.exists():
                    raise DistroNotFoundException(src_path)
                copy(src_path, dst_folder)
            cue_img_name = app_desc.distro.files[1]
            dbox = (DosBoxDos(dst_folder, app_desc, DosBoxDosConf(mod=DosBoxMod.X)),)
            dbox.mount(DosMountPointCD(letter=FIRST_CD_DRIVE_LETTER, path=dst_folder / cue_img_name))
            dbox.run(INSTALLER_EXEC_PATH)
            copy(CURRENT_DIR / "files" / "SOUND.SET", app_folder)
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
