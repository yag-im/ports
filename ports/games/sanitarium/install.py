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
        src_folder = app_desc.src_path()
        dst_path = app_desc.dst_path()
        dst_app_path = dst_path / "app"
        if app_desc.distro.format == "3CD":
            # going in reverse order so files from CD #1 overwrite the rest, see scummvm wiki
            # https://wiki.scummvm.org/index.php/Sanitarium
            # also make sure *_volume settings are explicitly set in scummvm.ini, or game will start muted
            src_paths = [src_folder / f for f in reversed(app_desc.distro.files)]
            for src_path in src_paths:
                if not src_path.exists():
                    raise DistroNotFoundException(src_path)
                unpack_disc_image(src_path, dst_app_path)
            ScummVm(dst_path, "asylum", lang=app_desc.lang, app_dir=dst_app_path / "Data").gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
