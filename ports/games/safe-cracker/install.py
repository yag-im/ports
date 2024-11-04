import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
)
from lib.dosbox.dosbox_conf import DosBoxFlavor
from lib.dosbox.dosbox_win9x import (
    DosBoxWin9x,
    DosBoxWin9xConf,
)
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer

# TODO: wine has a "golden" support for this game, but it doesn't work in a docker container -
# mouse movements are locked

APP_DRIVE_SIZE = 20
APP_EXEC_PATH = APP_DIR / "sc_eng.exe"
CURRENT_DIR = Path(__file__).resolve().parent
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "sc32inst.exe"


class Main(Installer):
    def get_exec_prefix(self, lang: str) -> str:
        if lang == "en":
            return "eng"
        elif lang == "es":
            return "spa"
        else:
            raise ValueError(f"Unknown language: {lang}")

    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_LETTER)
            dbox = DosBoxWin9x(
                dst_folder, app_desc, DosBoxWin9xConf(flavor=DosBoxFlavor.WIN95OSR25, app_drive_size=APP_DRIVE_SIZE)
            )
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files)))
            runexit = True
            if app_desc.year_released == 1997:
                dbox.run(FIRST_CD_DRIVE_DIR / "Qt32inst.exe")
                dbox.run(FIRST_CD_DRIVE_DIR / "Directx" / "setup.exe")
                runexit = False
            dbox.run(INSTALLER_EXEC_PATH, runexit=runexit)
            dbox.run(APP_DIR / f"sc_{self.get_exec_prefix(app_desc.lang)}.exe", mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
