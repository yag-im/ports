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
    unpack_archive,
    unpack_disc_image,
)
from lib.utils import move


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        # https://wiki.scummvm.org/index.php/Discworld_II:_Missing_Presumed...!%3F
        if app_desc.distro.format == "2CD":
            src_folder = app_desc.src_path()
            dst_path = app_desc.dst_path()
            dst_app_path = dst_path / "app"
            lng = app_desc.lang[-2:]  # en-us -> us
            for idx, img_file in enumerate(app_desc.distro.files):
                src_path = src_folder / img_file
                if not src_path.exists():
                    raise DistroNotFoundException(src_path)
                if app_desc.lang == "es":
                    # spanish version contains all lang files fixes
                    unpack_archive(src_path, dst_app_path / "DW2")
                else:
                    unpack_disc_image(src_path, dst_app_path)
                    self.fix_lang_files(dst_app_path, app_desc.lang, idx + 1)
            ScummVm(dst_path, "tinsel:dw2", lang=lng, app_dir=dst_app_path / "DW2").gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)

    def fix_lang_files(self, dst_app_path: Path, lng: str, idx: int) -> None:
        if lng == "us":
            filename = "US"
        elif lng in ["en", "ru", "es"]:
            filename = "ENGLISH"
        else:
            raise ValueError(f"Unknown language: {lng}")
        for ext in ("TXT", "SMP", "IDX"):
            move(dst_app_path / "DW2" / f"{filename}.{ext}", dst_app_path / "DW2" / f"{filename}{idx}.{ext}")


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
