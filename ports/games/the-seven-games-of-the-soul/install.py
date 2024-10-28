import json
import sys
import tempfile
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.unpack import unpack_disc_image
from lib.utils import (
    copy,
    replace,
)
from lib.wine.const import APP_DRIVE_LETTER
from lib.wine.wine import Wine

APP_EXEC = "Faust.exe"
CURRENT_DIR = Path(__file__).resolve().parent


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "4CD":
            src_folder = app_desc.src_path()
            dst_path = app_desc.dst_path()
            app_path = dst_path / APP_DRIVE_LETTER / "app"
            app_data_path = app_path / "data"
            w = Wine(dst_path)

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                unpack_disc_image(src_folder / app_desc.distro.files[0], tmp_dir_path, creates=tmp_dir_path / "DATA")
                app_data_path.mkdir(parents=True, exist_ok=False)
                copy(tmp_dir_path / "DATA", app_data_path, copy_tree=True)
                copy(app_data_path / "eng" / "sy.at3", app_data_path)
                for f in ["ames.ini", "aobj.ini", "arxrin3.fon", "Faust.exe", "fl.ini", "mmxImage.dll"]:
                    copy(tmp_dir_path / f, app_path)

            for img in app_desc.distro.files[1:]:
                unpack_disc_image(src_folder / img, app_path)

            copy(CURRENT_DIR / "files" / "cd.ini", app_data_path)

            replace(app_path / "fl.ini", "CDROM", ".\\\\")
            replace(app_path / "fl.ini", r"CHECKCD:\s+1", "CHECKCD: 0")
            replace(app_path / "fl.ini", r"CHECKLOADSAVE:\s+1", "CHECKLOADSAVE: 0")

            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
