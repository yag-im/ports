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
    MAME = "mame"  # MAME


class RetroArch:
    def __init__(self, root_dir, conf: dict | None = None) -> None:
        self.root_dir = root_dir
        self.conf = conf or {}

    def gen_run_script(self, core: RetroArchCore, file: str) -> Path:
        puae_model = self.conf.get("puae_model")
        if core == RetroArchCore.PUAE and puae_model and puae_model not in PUAE_KICKSTARTS:
            raise ValueError(f"Unknown PUAE model: {puae_model}")

        mame_driver = self.conf.get("mame_driver")
        cmd_file = None
        mame_cmd = None

        if core == RetroArchCore.MAME:
            if not mame_driver:
                raise ValueError("mame_driver is required for MAME core")

            mame_media = self.conf.get("mame_media", "-flop1")
            mame_rp = (
                self.conf.get("mame_rp")
                or self.conf.get("mame_bios_dir")
                or "/home/gamer/.config/retroarch/system/mame/roms"
            )
            mame_autoboot_delay = self.conf.get("mame_autoboot_delay", 2)

            file_stem = Path(file).stem
            mame_autoboot_cmd = self.conf.get("mame_autoboot_command")
            if mame_autoboot_cmd is None:
                mame_autoboot_cmd = f'LOADM"{file_stem}":EXEC\\n'
            elif isinstance(mame_autoboot_cmd, str) and "{stem}" in mame_autoboot_cmd:
                mame_autoboot_cmd = mame_autoboot_cmd.format(stem=file_stem, file=file)

            cmd_parts = [mame_driver]
            if mame_media:
                cmd_parts.append(f'{mame_media} "{file}"')
            else:
                cmd_parts.append(f'"{file}"')

            if mame_rp:
                cmd_parts.append(f'-rp "{mame_rp}"')

            if mame_autoboot_delay is not None:
                cmd_parts.append(f"-autoboot_delay {mame_autoboot_delay}")

            if mame_autoboot_cmd:
                if " " not in mame_autoboot_cmd and not (
                    mame_autoboot_cmd.startswith('"') and mame_autoboot_cmd.endswith('"')
                ):
                    cmd_parts.append(f"-autoboot_command {mame_autoboot_cmd}")
                else:
                    escaped_autoboot_cmd = mame_autoboot_cmd.replace('"', '""')
                    cmd_parts.append(f'-autoboot_command "{escaped_autoboot_cmd}"')

            mame_cmd = " ".join(cmd_parts)

            cmd_file = f"{file_stem}.cmd"
            cmd_path = self.root_dir / cmd_file
            cmd_path.write_text(f"{mame_cmd}\n")

        tmpl_params = {
            "libretro": core.value,
            "file": file,
            "puae_model": puae_model,
            "puae_kickstart": PUAE_KICKSTARTS.get(puae_model),
            "mame_driver": mame_driver,
            "mame_cmd": mame_cmd,
            "cmd_file": cmd_file,
        }
        output_path = self.root_dir / "run.sh"
        template(CURRENT_DIR / "templates" / "run.sh.tmpl", output_path, params=tmpl_params)
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path
