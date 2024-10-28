import json
import sys
import tempfile
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox.const import APP_DRIVE_LETTER
from lib.errors import (
    DistroNotFoundException,
    UnknownDistroFormatException,
)
from lib.installer import Installer
from lib.unpack import (
    unpack_disc_image,
    unpack_innoextract,
)
from lib.utils import copy
from lib.wine.const import APP_DIR
from lib.wine.wine import Wine

APP_EXEC = "PILOTS.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        src_folder = app_desc.src_path()
        dst_folder = app_desc.dst_path()
        app_path = dst_folder / APP_DRIVE_LETTER / "app"
        src_path = src_folder / app_desc.distro.files[0]
        if not src_path.exists():
            raise DistroNotFoundException(src_path)
        if app_desc.distro.format == "1CD":
            w = Wine(dst_folder)
            unpack_disc_image(src_path, app_path)
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        elif app_desc.distro.format == "gog":
            w = Wine(dst_folder)
            app_path.mkdir(parents=True, exist_ok=False)
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                unpack_innoextract(
                    src_path, tmp_dir_path, tmp_dir_path / "app" / "bin" / "Pilot Brothers.exe", is_gog=True
                )
                copy(tmp_dir_path / "app", app_path, copy_tree=True)
            w.gen_run_script(app_exec="Pilot Brothers.exe", work_dir=APP_DIR / "bin")
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
