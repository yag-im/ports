import json
import sys

from lib.app_desc import AppDesc
from lib.dosbox.const import APP_DRIVE_LETTER
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.unpack import unpack_disc_image
from lib.wine.wine import Wine

APP_EXEC = "STRLIZ.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "1CD":
            src_folder = app_desc.src_path()
            img_file = app_desc.distro.files[0]
            src_path = src_folder / img_file
            if not src_path.exists():
                raise DistroNotFoundException(src_path)
            dst_path = app_desc.dst_path()
            w = Wine(dst_path)
            app_path = dst_path / APP_DRIVE_LETTER / "app"
            unpack_disc_image(src_path, app_path)
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
