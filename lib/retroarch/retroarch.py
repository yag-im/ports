import stat
from enum import StrEnum
from pathlib import Path

from lib.utils import template

CURRENT_DIR = Path(__file__).resolve().parent


class RetroArchCore(StrEnum):
    CDI = "same_cdi"


class RetroArch:
    def __init__(self, root_dir) -> None:
        self.root_dir = root_dir

    def map_core_libretro(self, core: RetroArchCore):
        if core == RetroArchCore.CDI:
            return "same_cdi_libretro.so"

    def gen_run_script(self, core: RetroArchCore, file: str) -> Path:
        tmpl_params = {
            "libretro": self.map_core_libretro(core),
            "file": file,
        }
        output_path = self.root_dir / "run.sh"
        template(CURRENT_DIR / "templates" / "run.sh.tmpl", output_path, params=tmpl_params)
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path
