import json
import sys

from lib.app_desc import AppDesc
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
from lib.wine.const import (
    APP_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_LETTER,
)
from lib.wine.wine import Wine

APP_EXEC = "engine.exe"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_folder = app_desc.dst_path()
        if app_desc.distro.format == "3CD":
            w = Wine(dst_folder)
            app_path = dst_folder / APP_DRIVE_LETTER / "app"
            app_path.mkdir()
            for f in app_desc.distro.files:
                src_path = src_folder / f
                if not src_path.exists():
                    raise DistroNotFoundException(src_path)
                unpack_disc_image(src_path, dst_folder / app_path)
            cd_dir = dst_folder / FIRST_CD_DRIVE_LETTER
            cd_dir.mkdir()
            work_dir = app_path / "engine" / "linc"
            wine_work_dir = APP_DIR / "engine" / "linc"
            # app requires "movies" on CD
            move(app_path / "movies", cd_dir)
            w.add_cdrom(FIRST_CD_DRIVE_LETTER, cd_dir)
            # with "minimum" app just exits and empties "m" folder
            rm(work_dir / "minimum")
            w.gen_run_script(app_exec=APP_EXEC, work_dir=wine_work_dir)
            # game checks for CD presence by label
            # wine doesn't support manual labels definitions for CDs
            # TODO: fix GetVolumeInformationA() so it honors mount mgrs' labels
            # 0x410EE8: JNZ <- NOP
            copy(src_folder / "patch" / APP_EXEC, work_dir)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
