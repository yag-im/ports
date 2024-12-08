import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.utils import (
    copy,
    move,
    rm,
)
from lib.wine.const import (
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE,
    FIRST_CD_DRIVE_LETTER,
)
from lib.wine.helpers import unpack_cds_as_letters
from lib.wine.wine import (
    OsVer,
    VirtualDesktopResolution,
    Wine,
)

APP_EXEC = "titanic.exe"
CURRENT_DIR = Path(__file__).resolve().parent

# this app is fun: installs only on win95/xp, but runs only on win7 with quicktime7


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "3CD":
            src_folder = app_desc.src_path()
            dst_folder = app_desc.dst_path()
            app_folder = dst_folder / APP_DRIVE_LETTER / "app"
            unpack_cds_as_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_DRIVE_LETTER)
            w = Wine(dst_folder, os_ver=OsVer.WINDOWSXP)
            w.add_cdrom(FIRST_CD_DRIVE_LETTER, dst_folder / FIRST_CD_DRIVE_LETTER)
            # install into D:\app, skip QT install at the end
            w.run(FIRST_CD_DRIVE / "Install.exe", virtual_desktop=VirtualDesktopResolution.RES_640_480)
            cd_letter = FIRST_CD_DRIVE_LETTER
            for i in range(1, 4):
                move(dst_folder / cd_letter / f"DATA{i}", app_folder / "data")
                rm(dst_folder / cd_letter)  # TODO: use w.remove_cdrom() instead
                cd_letter = chr(ord(cd_letter) + 1)
            copy(CURRENT_DIR / "files" / "*.ini", app_folder)
            w.run_winetricks("win7")
            # for QT set "Safe mode: GDI only" at the end on the "Advanced" tab
            w.run_winetricks("quicktime76", quiet=False)
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
