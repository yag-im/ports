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
from lib.scummvm.scummvm import ScummVm
from lib.unpack import (
    unpack_archive,
    unpack_innoextract,
)
from lib.utils import copy


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "innosetup":
            src_folder = app_desc.src_path()
            img_file = app_desc.distro.files[0]
            src_path = src_folder / img_file
            if not src_path.exists():
                raise DistroNotFoundException(src_path)
            dst_path = app_desc.dst_path()
            dst_app_path = dst_path / "app"
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                unpack_innoextract(src_path, tmp_dir_path, tmp_dir_path / "app" / "bsengine.exe", is_gog=False)
                copy(tmp_dir_path / "app", dst_path)
            unpack_archive(src_folder / app_desc.distro.files[1], dst_app_path)
            ScummVm(dst_path, "sword25", lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
