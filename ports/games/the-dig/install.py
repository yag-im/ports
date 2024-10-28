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
from lib.utils import (
    move,
    rm,
)

CURRENT_DIR = Path(__file__).resolve().parent

SCUMMVM_GAME = "dig"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_path = app_desc.dst_path()
        dst_app_path = dst_path / "app"
        dst_app_path.mkdir(exist_ok=False, parents=True)
        if app_desc.distro.format == "1CD":
            src_path = src_folder / app_desc.distro.files[0]
            if not src_path.exists():
                raise DistroNotFoundException(src_path)
            unpack_disc_image(
                src_path,
                dst_app_path,
                ["DIG/VIDEO", "DIG/DIG.LA0", "DIG/DIG.LA1", "DIG/DIGMUSIC.BUN", "DIG/DIGVOICE.BUN"],
            )
            move(dst_app_path / "DIG" / "*", dst_app_path)
            rm(dst_app_path / "DIG")
            # https://wiki.scummvm.org/index.php?title=The_Dig
            ScummVm(dst_path, SCUMMVM_GAME, lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
