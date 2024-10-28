import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.scummvm.scummvm import ScummVm
from lib.unpack import unpack_disc_image
from lib.utils import copy

CURRENT_DIR = Path(__file__).resolve().parent


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_path = app_desc.dst_path()
        dst_app_path = dst_path / "app"
        if app_desc.distro.format == "3CD":
            src_paths = [src_folder / f for f in app_desc.distro.files[:3]]
            ix = 1
            for src_path in src_paths:
                if not src_path.exists():
                    raise DistroNotFoundException(src_path)
                unpack_disc_image(src_path, dst_app_path, [f"CD{ix}.HPF"])
                ix += 1
            copy(src_folder / app_desc.distro.files[3], dst_app_path)
            # https://wiki.scummvm.org/index.php/The_Last_Express
            ScummVm(dst_path, "lastexpress", lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
