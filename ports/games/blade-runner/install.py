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
    unpack_disc_image,
)
from lib.utils import (
    copy,
    move,
)

# https://wiki.scummvm.org/index.php?title=Blade_Runner


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        src_folder = app_desc.src_path()
        dst_path = app_desc.dst_path()
        dst_app_path = dst_path / "app"
        if app_desc.distro.format == "4CD":
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                src_paths = [src_folder / f for f in app_desc.distro.files]
                for src_path in src_paths:
                    if not src_path.exists():
                        raise DistroNotFoundException(src_path)
                    unpack_disc_image(src_path, tmp_dir_path)
                unpack_archive(src_folder / "Blade_Runner_Subtitles-v8.zip", tmp_dir_path)

                copy(tmp_dir_path / "CD1", dst_app_path, copy_tree=True)
                move(dst_app_path / "CDFRAMES.DAT", dst_app_path / "CDFRAMES1.DAT")
                copy(tmp_dir_path / "BASE" / "COREANIM.DAT", dst_app_path)
                copy(tmp_dir_path / "BASE" / "MODE.MIX", dst_app_path)
                copy(tmp_dir_path / "BASE" / "MUSIC.MIX", dst_app_path)
                copy(tmp_dir_path / "BASE" / "SFX.MIX", dst_app_path)
                copy(tmp_dir_path / "BASE" / "SPCHSFX.TLK", dst_app_path)
                copy(tmp_dir_path / "BASE" / "STARTUP.MIX", dst_app_path)

                copy(tmp_dir_path / "CD2", dst_app_path, copy_tree=True)
                move(dst_app_path / "CDFRAMES.DAT", dst_app_path / "CDFRAMES2.DAT")

                copy(tmp_dir_path / "CD3", dst_app_path, copy_tree=True)
                move(dst_app_path / "CDFRAMES.DAT", dst_app_path / "CDFRAMES3.DAT")

                copy(tmp_dir_path / "CD4", dst_app_path, copy_tree=True)
                move(dst_app_path / "CDFRAMES.DAT", dst_app_path / "CDFRAMES4.DAT")

                copy(tmp_dir_path / "SUBTITLES.MIX", dst_app_path)

            ScummVm(dst_path, "bladerunner", lang=app_desc.lang).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
