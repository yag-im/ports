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
from lib.unpack import (
    unpack_disc_image,
    unpack_innoextract,
)
from lib.utils import copy
from lib.wine.wine import Wine

CURRENT_DIR = Path(__file__).resolve().parent

APP_EXEC = "v32win.exe"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_path = app_desc.dst_path()
        dst_app_path = dst_path / "app"
        if app_desc.distro.format == "4CD":
            src_paths = [src_folder / f for f in app_desc.distro.files]
            for src_path in src_paths:
                if not src_path.exists():
                    raise DistroNotFoundException(src_path)
                unpack_disc_image(src_path, dst_app_path)
            # https://wiki.scummvm.org/index.php/The_11th_Hour
            ScummVm(dst_path, "groovie:11h", lang=app_desc.lang).gen_run_script()
        elif app_desc.distro.format == "gog":
            src_path = src_folder / app_desc.distro.files[0]
            unpack_innoextract(src_path, dst_app_path, creates=dst_app_path / APP_EXEC, is_gog=True)
            copy(CURRENT_DIR / "files" / "groovie2.ini", dst_app_path)
            w = Wine(dst_path)
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
