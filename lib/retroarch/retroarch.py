import stat
from enum import StrEnum
from pathlib import Path

from lib.utils import template

CURRENT_DIR = Path(__file__).resolve().parent


class RetroArchCore(StrEnum):
    SAME_CDI = "same_cdi"  # Philips CD-I
    FUSE = "fuse"  # ZX Spectrum
    VICE_X64 = "vice_x64"  # Commodore 64 (fast)


class RetroArch:
    def __init__(self, root_dir) -> None:
        self.root_dir = root_dir

    def gen_run_script(self, core: RetroArchCore, file: str) -> Path:
        tmpl_params = {
            "libretro": core.value,
            "file": file,
        }
        output_path = self.root_dir / "run.sh"
        template(CURRENT_DIR / "templates" / "run.sh.tmpl", output_path, params=tmpl_params)
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path
