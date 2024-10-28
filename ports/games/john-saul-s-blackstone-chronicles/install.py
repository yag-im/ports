import json
import sys

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.unpack import unpack_archive
from lib.utils import (
    copy,
    rm,
)
from lib.wine.const import (
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
    SECOND_CD_LETTER,
)
from lib.wine.helpers import unpack_cds_as_letters
from lib.wine.wine import Wine

APP_EXEC = "BSC.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        if app_desc.distro.format == "2CD":
            src_dir = app_desc.src_path()
            dst_dir = app_desc.dst_path()
            app_path = dst_dir / APP_DRIVE_LETTER / "app"
            w = Wine(dst_dir, lang=app_desc.lang)
            unpack_cds_as_letters(src_dir, dst_dir, app_desc.distro.files, FIRST_CD_LETTER)
            # make full install into D:\app with additional images
            unpack_archive(dst_dir / FIRST_CD_LETTER / "data1.cab", app_path)
            copy(dst_dir / FIRST_CD_LETTER / "BSC" / "*.PIC", app_path)
            # QT3 install (select "custom", uncheck everything except QuickTime itself at the top), ignore errors
            w.add_cdrom(FIRST_CD_LETTER, dst_dir / FIRST_CD_LETTER)
            w.run(FIRST_CD_DRIVE_DIR / "QuickTime" / "QuickTime30.exe")
            rm(dst_dir / FIRST_CD_LETTER)  # TODO: use w.remove_cdrom() instead when it's implemented
            # hi-res videos are on the CD2 so using it
            w.add_cdrom(SECOND_CD_LETTER, dst_dir / SECOND_CD_LETTER)
            w.upd_reg(
                {
                    "HKEY_LOCAL_MACHINE\\Software\\Red Orb Entertainment\\John Saul's Blackstone Chronicles\\1.0": [
                        {"Disc": "2"},
                    ]
                }
            )
            w.gen_run_script(app_exec=APP_EXEC)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
