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

CURRENT_DIR = Path(__file__).resolve().parent

SCUMMVM_GAME = "trecision:nl"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_path = app_desc.dst_path()
        dst_app_path = dst_path / "app"
        dst_app_path.mkdir(exist_ok=False, parents=True)
        if app_desc.distro.format == "3CD":
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                for f in app_desc.distro.files:
                    src_path = src_folder / f
                    if not src_path.exists():
                        raise DistroNotFoundException(src_path)
                    unpack_disc_image(src_path, tmp_path)
                copy([tmp_path / "AUTORUN", tmp_path / "FMV", tmp_path / "DATA"], dst_app_path)
            # https://wiki.scummvm.org/index.php?title=Nightlong:_Union_City_Conspiracy
            ScummVm(dst_path, SCUMMVM_GAME, lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
