import stat
from enum import StrEnum
from pathlib import Path

from lib.utils import template

CURRENT_DIR = Path(__file__).resolve().parent
PUAE_KICKSTARTS = {
    "A500": "kick34005.A500",
    "A1200": "kick40068.A1200",
}


class RetroArchCore(StrEnum):
    SAME_CDI = "same_cdi"  # Philips CD-I
    FUSE = "fuse"  # ZX Spectrum
    VICE_X64 = "vice_x64"  # Commodore 64 (fast)
    SEGA_GENESIS = "genesis_plus_gx"  # Sega Genesis/Mega Drive
    PUAE = "puae"  # Amiga


class RetroArch:
    def __init__(self, root_dir, conf: dict | None = None) -> None:
        self.root_dir = root_dir
        self.conf = conf or {}

    def gen_run_script(self, core: RetroArchCore, file: str) -> Path:
        puae_model = self.conf.get("puae_model")
        if core == RetroArchCore.PUAE and puae_model and puae_model not in PUAE_KICKSTARTS:
            raise ValueError(f"Unknown PUAE model: {puae_model}")
        tmpl_params = {
            "libretro": core.value,
            "file": file,
            "puae_model": puae_model,
            "puae_kickstart": PUAE_KICKSTARTS.get(puae_model),
        }
        output_path = self.root_dir / "run.sh"
        template(CURRENT_DIR / "templates" / "run.sh.tmpl", output_path, params=tmpl_params)
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path
