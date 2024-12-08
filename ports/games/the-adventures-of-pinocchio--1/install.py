import json
import sys
import tempfile
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    FIRST_CD_DRIVE,
    FIRST_CD_DRIVE_LETTER,
)
from lib.dosbox.dosbox_win3x import DosBoxWin3x
from lib.dosbox.misc import DosMountPointCD
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.unpack import unpack_disc_image
from lib.utils import (
    copy,
    move,
    rm,
)

APP_EXEC_PATH = APP_DIR / "PINOC.EXE"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE / "SETUP.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()

        if app_desc.distro.format == "4CD":
            img_file = app_desc.distro.files[0]
            src_path = src_folder / img_file
            if not src_path.exists():
                raise DistroNotFoundException(src_path)
            copy(src_path, dst_folder / FIRST_CD_DRIVE_LETTER)
            dbox = DosBoxWin3x(dst_folder, app_desc)
            # proceed installing with all suggested deps")
            dbox.mount(DosMountPointCD(letter=FIRST_CD_DRIVE_LETTER, path=dst_folder / FIRST_CD_DRIVE_LETTER))
            dbox.run(path=INSTALLER_EXEC_PATH)
            rm(dst_folder / FIRST_CD_DRIVE_LETTER)
            dbox.umount(drive_letter=FIRST_CD_DRIVE_LETTER)
            # copy all AVI files into app folder
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_folder = Path(tmp_dir)
                for f in app_desc.distro.files:
                    src_path = src_folder / f
                    if not src_path.exists():
                        raise DistroNotFoundException(src_path)
                    unpack_disc_image(src_path, tmp_folder)
                move(tmp_folder / "*.AVI", dst_folder / "D" / "APP")
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
