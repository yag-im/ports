import json
import sys

from lib.app_desc import AppDesc
from lib.dosbox.const import FIRST_CD_DRIVE
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
from lib.wine.const import FIRST_CD_DRIVE_LETTER

# TODO: works on the hosts' wine and fails to start in dockers' wine
# maybe try v9.0.0.0 from packages?

APP_EXEC = "Agent.exe"
APP_DRIVE_SIZE = 100
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE / "Setup.exe"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_DRIVE_LETTER)
            dbox = DosBoxWin9x(
                dst_folder,
                DosBoxWin9xConf(flavor=DosBoxFlavor.WIN98SE, app_drive_size=APP_DRIVE_SIZE),
            )
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_DRIVE_LETTER, len(app_desc.distro.files)))
            dbox.run(FIRST_CD_DRIVE / "Support" / "DX7Aeng.exe")
            dbox.run(FIRST_CD_DRIVE / "Support" / "iv5setup.exe")
            dbox.run(INSTALLER_EXEC_PATH)
            dbox.run(APP_EXEC, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


# class Main(Installer):
#     def __init__(self, app_desc: AppDesc):
#         super().__init__(app_desc)
#         if app_desc.distro.format == "1CD":
#             src_dir = app_desc.src_path()
#             dst_dir = app_desc.dst_path()
#             w = Wine(dst_dir, lang=app_desc.lang)
#             unpack_cds_as_letters(src_dir, dst_dir, app_desc.distro.files, FIRST_CD_DRIVE_LETTER)
#             w.add_cdrom(FIRST_CD_DRIVE_LETTER, dst_dir / FIRST_CD_DRIVE_LETTER)
#             # make full install into D:\app
#             w.run(INSTALLER_EXEC_PATH)
#             w.gen_run_script(app_exec=APP_EXEC)
#         else:
#             raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
