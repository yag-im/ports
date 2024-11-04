import json
import sys

from lib.app_desc import AppDesc
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.unpack import unpack_disc_image
from lib.utils import copy
from lib.wine.const import (
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
)
from lib.wine.helpers import unmount_cds
from lib.wine.wine import (
    VirtualDesktopResolution,
    Wine,
)


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        if app_desc.distro.format == "1CD":
            src_folder = app_desc.src_path()
            dst_folder = app_desc.dst_path()
            if app_desc.lang == "pl":
                app_exec = "CODE.EXE"
                unpack_disc_image(
                    src_folder / app_desc.distro.files[0],
                    dst_folder / FIRST_CD_LETTER,
                    extract_files=[
                        "DATA",
                    ],
                )
                w = Wine(dst_folder, lang=app_desc.lang)
                w.add_cdrom(FIRST_CD_LETTER, dst_folder / FIRST_CD_LETTER)
                # app looks for all files on the drive of type CD and runs from there, no D:\app dir is required
                # copy patched version of CODE.EXE (fixes "App relies on the Carry flag state after calling llseek" bug)
                copy(src_folder / app_exec, dst_folder / FIRST_CD_LETTER / "DATA")
                w.gen_run_script(app_exec=app_exec, work_dir=FIRST_CD_DRIVE_DIR / "DATA")
            elif app_desc.lang == "ru":
                app_exec = "gal.exe"
                unpack_disc_image(src_folder / app_desc.distro.files[0], dst_folder / FIRST_CD_LETTER)
                w = Wine(dst_folder, lang=app_desc.lang)
                w.add_cdrom(FIRST_CD_LETTER, dst_folder / FIRST_CD_LETTER)
                # make full install into D:\app
                w.run(FIRST_CD_DRIVE_DIR / "autorun.exe", virtual_desktop=VirtualDesktopResolution.RES_640_480)
                unmount_cds(w, dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files))
                # patch from https://www.old-games.ru/game/download/1942.html (modified, fix for Carry flag, see above)
                copy(src_folder / "patch" / "gal-mod.exe", dst_folder / APP_DRIVE_LETTER / "app" / app_exec)
                w.gen_run_script(app_exec=app_exec)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
