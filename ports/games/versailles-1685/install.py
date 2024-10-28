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
from lib.unpack import unpack_disc_image
from lib.utils import copy


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        if app_desc.distro.format == "2CD":
            src_folder = app_desc.src_path()
            src_paths = [src_folder / f for f in app_desc.distro.files]
            dst_path = app_desc.dst_path()
            dst_app_path = dst_path / "app"
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                for src_path in src_paths:
                    if not src_path.exists():
                        raise DistroNotFoundException(src_path)
                    unpack_disc_image(src_path, tmp_dir_path)
                # https://wiki.scummvm.org/index.php/Versailles_1685
                copy(tmp_dir_path / "DATAS_V", dst_app_path, copy_tree=True)
                copy(tmp_dir_path / "INSTALL" / "DATA", dst_app_path, copy_tree=True)
                copy(tmp_dir_path / "INSTALL" / "DOS" / "VERSAILL.PGM", dst_app_path)
            ScummVm(dst_path, "cryomni3d:versailles", lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
