import json
import sys
import tempfile
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.scummvm.scummvm import ScummVm
from lib.unpack import unpack_disc_image
from lib.utils import move

# https://wiki.scummvm.org/index.php?title=Broken_Sword_1
SCUMMVM_GAME = "sword1:sword1"


class Main(Installer):
    @staticmethod
    def get_scummvm_lang(lang: str):
        if lang == "en":
            return "gb"
        else:
            return lang

    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)

        if app_desc.distro.format == "2CD":
            src_folder = app_desc.src_path()
            dst_path = app_desc.dst_path()
            dst_app_path = dst_path / "app"
            for ix, f in enumerate(app_desc.distro.files):
                if app_desc.lang == "ru" and ix == 1:
                    continue  # spec handling for RU/CD2 below
                unpack_disc_image(src_folder / f, dst_app_path, ["CLUSTERS", "MUSIC", "SMACKSHI", "SPEECH"])
                move(dst_app_path / "SPEECH" / "SPEECH.CLU", dst_app_path / "SPEECH" / f"SPEECH{ix+1}.CLU")
            if app_desc.lang == "ru":
                f = app_desc.distro.files[0]
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_path = Path(tmp_dir)
                    ru_cd2_files = ["Clusters", "Music", "Smackshi", "Speech"]
                    unpack_disc_image(src_folder / f, tmp_path, ru_cd2_files)
                    for f in ru_cd2_files:
                        move(tmp_path / f / "*", dst_app_path / f.upper())
                    move(dst_app_path / "SPEECH" / "SPEECH.CLU", dst_app_path / "SPEECH" / "SPEECH2.CLU")

            ScummVm(dst_path, SCUMMVM_GAME, lang=Main.get_scummvm_lang(app_desc.lang)).gen_run_script()
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
