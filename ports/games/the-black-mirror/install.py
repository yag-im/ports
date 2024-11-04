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
from lib.unpack import unpack_innoextract
from lib.utils import (
    copy,
    replace,
)
from lib.wine.const import APP_DRIVE_LETTER
from lib.wine.wine import (
    VirtualDesktopResolution,
    Wine,
)

APP_EXEC = "BMirror.exe"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "gog":
            src_folder = app_desc.src_path()
            img_file = app_desc.distro.files[0]
            src_path = src_folder / img_file
            if not src_path.exists():
                raise DistroNotFoundException(src_path)
            dst_path = app_desc.dst_path()
            app_path = dst_path / APP_DRIVE_LETTER / "app"
            w = Wine(dst_path, virtual_desktop=VirtualDesktopResolution.RES_800_600)
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                unpack_innoextract(src_path, tmp_dir_path, tmp_dir_path / "app" / APP_EXEC, is_gog=False)
                copy(tmp_dir_path / "app", dst_path / APP_DRIVE_LETTER)
            replace(app_path / "agds.cfg", "videomode=800x600x32", "videomode=800x600x16")
            w.gen_run_script(
                app_exec=APP_EXEC,
            )
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
