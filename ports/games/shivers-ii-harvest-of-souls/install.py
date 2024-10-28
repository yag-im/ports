import json
import sys
import tempfile
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
)
from lib.dosbox.dosbox_win3x import DosBoxWin3x
from lib.dosbox.misc import DosMountPointCD
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.unpack import (
    unpack_disc_image,
    unpack_innoextract,
)
from lib.utils import copy
from lib.wine.const import APP_DRIVE_LETTER
from lib.wine.wine import Wine

APP_EXEC = "RSHIVERS.EXE"
APP_EXEC_PATH = APP_DIR / "SIERRA" / "SHIVERS2" / APP_EXEC
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "SETUP.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "2CD":
            # TODO
            # rshivers exits properly, shivers2 leaves win311 running
            # rshivers doesn't show startup banner, shivers2 does
            # rshivers doesn't ask to exit game at the beginning, shivers2 does
            # require to press F5 to animate Steve at the beginning
            dbox = DosBoxWin3x(dst_folder, app_desc)
            app_path = dst_folder / APP_DRIVE_LETTER / "app"
            app_path.mkdir(parents=True)

            first_cd_drive_path = dst_folder / FIRST_CD_LETTER
            unpack_disc_image(src_folder / app_desc.distro.files[0], first_cd_drive_path)
            unpack_disc_image(src_folder / app_desc.distro.files[2], first_cd_drive_path)
            dbox.mount(DosMountPointCD(letter=FIRST_CD_LETTER, path=dst_folder / FIRST_CD_LETTER))

            # proceed installing into D:\app\SIERRA\SHIVERS2, skip system check as it hangs")
            dbox.run(INSTALLER_EXEC_PATH, exit=False)
            # patch removes startup delay (some timer based performance checks) at 0x413851
            # TODO: make all videos play fullscreen by default (currently requires manual F5 press)
            copy(src_folder / "patches" / "RSHIVERS.EXE", app_path / "SIERRA" / "SHIVERS2")
            dbox.run(APP_EXEC_PATH, mock=True)
        elif app_desc.distro.format == "gog":
            # TODO: videoplayer freezes at startup on prod
            w = Wine(dst_folder)
            app_path = dst_folder / APP_DRIVE_LETTER / "app"
            app_path.mkdir(parents=True)
            src_path = src_folder / app_desc.distro.files[0]
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                unpack_innoextract(src_path, tmp_dir_path, tmp_dir_path / APP_EXEC, is_gog=True)
                copy(
                    [
                        tmp_dir_path / "DATA",
                        tmp_dir_path / "ROBOTS",
                        tmp_dir_path / "MOVIES",
                        tmp_dir_path / "DLL",
                        tmp_dir_path / "RESMAP.*",
                        tmp_dir_path / "RESOURCE.SFX",
                        tmp_dir_path / "LANGUAGE.INF",
                        tmp_dir_path / "SIERRA.ERR",
                        tmp_dir_path / "ddraw.dll",
                        tmp_dir_path / "10908.AUD",
                        tmp_dir_path / "S2SYSR.DLL",
                        tmp_dir_path / "RSHIVERS.EXE",
                        tmp_dir_path / "RESSCI.*",
                        tmp_dir_path / "RESOURCE.WIN",
                        tmp_dir_path / "RESMDT.*",
                        tmp_dir_path / "GAMESYSR.DLL",
                    ],
                    app_path,
                )
            w.gen_run_script(app_exec=APP_EXEC)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
