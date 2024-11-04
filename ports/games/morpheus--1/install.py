import json
import sys

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.wine.const import (
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
    SECOND_CD_LETTER,
    THIRD_CD_LETTER,
)
from lib.wine.helpers import unpack_cds_as_letters
from lib.wine.wine import (
    VirtualDesktopResolution,
    Wine,
)

APP_EXEC = "Morpheus.exe"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        if app_desc.distro.format == "3CD":
            src_folder = app_desc.src_path()
            dst_folder = app_desc.dst_path()
            unpack_cds_as_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_LETTER)
            w = Wine(dst_folder)
            w.add_cdrom(FIRST_CD_LETTER, dst_folder / FIRST_CD_LETTER)
            w.add_cdrom(SECOND_CD_LETTER, dst_folder / SECOND_CD_LETTER)
            w.add_cdrom(THIRD_CD_LETTER, dst_folder / THIRD_CD_LETTER)
            # install into D:\app, ignore QT install errors, there are few
            w.run(FIRST_CD_DRIVE_DIR / "Setup.exe", virtual_desktop=VirtualDesktopResolution.RES_640_480)
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
