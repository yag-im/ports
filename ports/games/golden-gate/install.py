import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.unpack import unpack_disc_image
from lib.utils import copy
from lib.wine.const import (
    APP_DRIVE_LETTER,
    FIRST_CD_LETTER,
)
from lib.wine.wine import (
    OsVer,
    Wine,
)

APP_EXEC = "GOLDENGA.EXE"
# APP_EXEC_PATCH is an official patch with another manual patch on top of it (emulates fake HIGH video mode in wine,
# avoiding a MessageBox popup on a starup).
APP_EXEC_PATCH = "GOLDENGA.EXE-patch-mod"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_folder = app_desc.dst_path()
        app_drive_folder = dst_folder / APP_DRIVE_LETTER
        if app_desc.distro.format == "1CD":
            src_path = src_folder / app_desc.distro.files[0]
            if not src_path.exists():
                raise DistroNotFoundException(src_path)
            w = Wine(dst_folder, os_ver=OsVer.WINDOWS95)
            unpack_disc_image(
                src_path,
                dst_folder / FIRST_CD_LETTER,
                extract_files=[
                    "NEWMLIST.TXT",
                    "GGVARS",
                    "GGSYSTBL",
                    "GOLDEN",
                    "QTIME32",
                ],
            )
            w.add_cdrom(FIRST_CD_LETTER, dst_folder / FIRST_CD_LETTER)
            w.run(dst_folder / FIRST_CD_LETTER / "QTIME32" / "QT32INST.EXE", virtual_desktop=None)
            # rm(dst_folder / FIRST_CD_LETTER / "QTIME32") TODO: this hangs cos QT remains opened, so remove manually
            Path(app_drive_folder / "app").mkdir()
            copy(src_folder / "patch" / APP_EXEC_PATCH, app_drive_folder / "app" / APP_EXEC)
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
