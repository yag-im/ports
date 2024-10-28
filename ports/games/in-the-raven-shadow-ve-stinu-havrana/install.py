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
    APP_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_LETTER,
)
from lib.wine.helpers import unpack_cds_as_letters
from lib.wine.wine import (
    OsVer,
    Wine,
)

APP_EXEC_RU = "In The Raven Shadow.exe"
APP_EXEC_CS = "Ve stínu havrana.exe"
CURRENT_DIR = Path(__file__).resolve().parent


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "1CD":
            src_dir = app_desc.src_path()
            dst_dir = app_desc.dst_path()
            app_dir = dst_dir / APP_DRIVE_LETTER / "app"

            w = Wine(dst_dir, os_ver=OsVer.WINDOWS95, lang=app_desc.lang)
            w.run_winetricks("renderer=no3d")  # remove if 3D adapter is available

            unpack_cds_as_letters(src_dir, dst_dir, app_desc.distro.files, FIRST_CD_LETTER)
            app_dir.mkdir()
            if app_desc.lang == "ru":
                app_exec = APP_EXEC_RU
                copy(dst_dir / FIRST_CD_LETTER / "cd data", app_dir / "Data")
                move(app_dir / "Data" / "*.dll", app_dir)
                # mock CD label checks. Also *avi files must be present in Data dir
                copy(src_dir / "patch" / app_exec, app_dir)
                rm(dst_dir / FIRST_CD_LETTER)
                fate_ins_content = str(APP_DIR)
            elif app_desc.lang == "cs":
                (app_dir / "Data").mkdir()
                app_exec = APP_EXEC_CS
                copy(dst_dir / FIRST_CD_LETTER / "Cd Data" / "*.AFV", app_dir / "Data")
                copy(dst_dir / FIRST_CD_LETTER / "Cd Data" / "DSETUP.DLL", app_dir)
                copy(dst_dir / FIRST_CD_LETTER / "Cd Data" / "EX.XXX", app_dir / app_exec)
                w.add_cdrom(FIRST_CD_LETTER, dst_dir / FIRST_CD_LETTER, label="Havran")
                fate_ins_content = str(APP_DIR / "Data")
            with open(dst_dir / ".wine" / "drive_c" / "windows" / "fate.ins", "wb") as f:
                f.write(fate_ins_content.encode("UTF-8"))
            w.gen_run_script(
                app_exec=app_exec,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
