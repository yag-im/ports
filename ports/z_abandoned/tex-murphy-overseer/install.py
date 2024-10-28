import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.unpack import unpack_archive
from lib.utils import (
    copy,
    rm,
)
from lib.wine.const import (
    APP_DRIVE_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
)
from lib.wine.helpers import unpack_cds_as_letters
from lib.wine.wine import (
    OsVer,
    VirtualDesktopResolution,
    Wine,
)

# TODO: DVD version doesn't start, try 5CD version

APP_EXEC = "OVERSEER.EXE"

CURRENT_DIR = Path(__file__).resolve().parent


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        src_dir = app_desc.src_path()
        dst_dir = app_desc.dst_path()
        app_path = dst_dir / APP_DRIVE_LETTER / "app"
        if app_desc.distro.format == "1DVD":
            unpack_cds_as_letters(src_dir, dst_dir, app_desc.distro.files, FIRST_CD_LETTER)
            w = Wine(dst_dir, os_ver=OsVer.WINDOWS98, virtual_desktop=VirtualDesktopResolution.RES_800x600)
            w.add_cdrom(FIRST_CD_LETTER, dst_dir / FIRST_CD_LETTER)
            w.run(FIRST_CD_DRIVE_DIR / "SETUP.EXE")
            # install into D:\app, install RSX3D sound, do not install DirectX 5
            unpack_archive(src_dir / "patch" / "tex5b104.zip", dst_dir / APP_DRIVE_LETTER / "patch")
            w.run(APP_DRIVE_DIR / "patch" / "UPDATE.EXE")
            rm(dst_dir / APP_DRIVE_LETTER / "patch")
            copy(CURRENT_DIR / "files" / "Tex.ini", app_path)
            w.run_winetricks(OsVer.WINDOWSXP.value)
            w.run_winetricks("lavfilters702")
            w.run_winetricks("ffdshow")
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
