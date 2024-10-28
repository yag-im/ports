import json
import sys
import tempfile
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.scummvm.scummvm import ScummVm
from lib.unpack import unpack_disc_image
from lib.utils import (
    copy,
    move,
)

# https://wiki.scummvm.org/index.php?title=Broken_Sword_2
SCUMMVM_GAME = "sword2:sword2"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "2CD":
            src_folder = app_desc.src_path()
            dst_path = app_desc.dst_path()
            dst_app_path = dst_path / "app"
            dst_app_path.mkdir()
            for ix, f in enumerate(app_desc.distro.files):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_dir_path = Path(tmp_dir)
                    unpack_disc_image(src_folder / f, tmp_dir_path)
                    copy(
                        [
                            tmp_dir_path / "Clusters" / "*.clu",
                            tmp_dir_path / "Smacks" / "*.smk",
                        ],
                        dst_app_path,
                    )
                    if ix == 0:
                        copy(
                            [
                                tmp_dir_path / "Sword2" / "*.inf",
                                tmp_dir_path / "Clusters" / "SCRIPTS.CLU",
                                tmp_dir_path / "Clusters" / "*.inf",
                                tmp_dir_path / "Clusters" / "*.tab",
                                tmp_dir_path / "Clusters" / "Credits.bmp",
                            ],
                            dst_app_path,
                        )
                    move(dst_app_path / "Music.clu", dst_app_path / f"Music{ix+1}.clu")
                    move(dst_app_path / "speech.clu", dst_app_path / f"speech{ix+1}.clu")

            ScummVm(dst_path, SCUMMVM_GAME, lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
