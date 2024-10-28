import json
import sys

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.scummvm.scummvm import ScummVm
from lib.unpack import unpack_disc_image
from lib.utils import (
    move,
    rm,
)


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "2CD":
            # https://wiki.scummvm.org/index.php/Lighthouse
            src_folder = app_desc.src_path()
            dst_path = app_desc.dst_path()
            dst_app_path = dst_path / "app"
            unpack_disc_image(src_folder / app_desc.distro.files[0], dst_app_path)
            move(dst_app_path / "RESOURCE.AUD", dst_app_path / "RESAUD.001")
            rm(dst_app_path / "DEMOS")
            rm(dst_app_path / "DIRECTX")
            unpack_disc_image(src_folder / app_desc.distro.files[1], dst_app_path)
            move(dst_app_path / "RESOURCE.AUD", dst_app_path / "RESAUD.002")
            ScummVm(dst_path, "sci", lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
