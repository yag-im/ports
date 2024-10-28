import json
import sys

from lib.app_desc import AppDesc
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.scummvm.scummvm import ScummVm
from lib.unpack import unpack_disc_image


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
            dst_app_path = dst_path / "app"
            unpack_disc_image(src_path, dst_app_path, creates=dst_app_path / "TEASER.EXE")
            ScummVm(dst_path, "pink:pokus", lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
