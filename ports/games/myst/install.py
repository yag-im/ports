import configparser
import json
import sys
from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.dosbox import DosBoxWin3x
from lib.dosbox.const import (
    APP_DIR,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
    SYSTEM_DRIVE_LETTER,
)
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer

APP_EXEC = "MYST.EXE"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "MSSETUP.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_LETTER)
            dbox = DosBoxWin3x(dst_folder, app_desc)
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files)))
            # proceed with a minimal CD installation
            dbox.run(INSTALLER_EXEC_PATH)
            # resolve QT conflict
            self.upd_qtw(dst_folder / SYSTEM_DRIVE_LETTER / "WINDOWS" / "QTW.INI")
            dbox.run(PureWindowsPath(APP_DIR / APP_EXEC), mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)

    def upd_qtw(self, qtw_ini_path: Path):
        config = configparser.ConfigParser()
        config.read(qtw_ini_path)
        config["Override"] = {"oldVersion": "1"}
        with open(qtw_ini_path, "w", newline="\r\n") as f:
            config.write(f, space_around_delimiters=False)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
