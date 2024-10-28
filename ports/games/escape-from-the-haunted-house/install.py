import json
import sys
import tempfile
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.unpack import unpack_disc_image
from lib.utils import copy
from lib.wine.const import APP_DRIVE_LETTER
from lib.wine.wine import Wine

APP_EXEC = "PARK.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_folder = app_desc.dst_path()
        app_path = dst_folder / APP_DRIVE_LETTER / "app"
        if app_desc.distro.format == "1CD":
            src_path = src_folder / app_desc.distro.files[0]
            if not src_path.exists():
                raise DistroNotFoundException(src_path)
            w = Wine(dst_folder)
            app_path.mkdir(exist_ok=False)
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                unpack_disc_image(src_path, tmp_dir_path)
                copy([tmp_dir_path / "PARK.EXE", tmp_dir_path / "PARK.IMV", tmp_dir_path / "*.DLL"], app_path)
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
