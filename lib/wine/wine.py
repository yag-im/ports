import os
import stat
import tempfile
import time
from collections import OrderedDict
from enum import (
    Enum,
    StrEnum,
)
from pathlib import (
    Path,
    PureWindowsPath,
)
from typing import (
    Dict,
    List,
    Union,
)

from lib.conf import (
    USER_GAMER,
    VIDEO_OUTPUT,
)
from lib.utils import (
    copy,
    run_cmd,
    str_in_file,
    template,
)
from lib.wine.const import (
    APP_DIR,
    APP_DRIVE_LETTER,
    RUNNERS_BUNDLES_BASE_DIR,
    SYSTEM_DRIVE,
)


class OsVer(Enum):
    WINDOWS95 = "win95"
    WINDOWS98 = "win98"
    WINDOWS7 = "win7"
    WINDOWSXP = "winxp"


class OsArch(Enum):
    WIN32 = "win32"
    WIN64 = "win64"


class VirtualDesktopResolution(Enum):
    RES_640_480 = "640x480"
    RES_800_600 = "800x600"
    RES_1024_768 = "1024x768"


DEFAULT_OS_VER = OsVer.WINDOWS7
DEFAULT_OS_ARCH = OsArch.WIN32
DEFAULT_WINE_VER = "10.0"

WINE_USER = "gamer"

CURRENT_DIR = Path(__file__).resolve().parent


class DriveType(StrEnum):
    CDROM = "cdrom"
    HD = "hd"


class Wine:
    def __init__(
        self,
        root_dir: Path,
        os_ver: OsVer = DEFAULT_OS_VER,
        os_arch: OsArch = DEFAULT_OS_ARCH,
        virtual_desktop: VirtualDesktopResolution = None,
        wine_ver: str = DEFAULT_WINE_VER,
        resolution: str = None,
        lang: str = "en",
    ) -> None:
        assert root_dir.exists()
        self.root_dir = root_dir
        self.prefix = root_dir / ".wine"
        self.virtual_desktop = virtual_desktop
        self.resolution = resolution
        self.lang = lang
        wine_env = {
            "WINEARCH": os_arch.value,
            "WINEPREFIX": str(self.prefix),
            "USER": WINE_USER,
            "LC_ALL": self._get_lang(),
        }
        self.wine_env = wine_env
        self.prefix.mkdir()
        copy(RUNNERS_BUNDLES_BASE_DIR / "wine" / wine_ver / os_arch.value, self.prefix, copy_tree=True)

        self.app_drive_dir = self.root_dir / APP_DRIVE_LETTER
        self.app_drive_dir.mkdir(exist_ok=False, parents=True)
        self.add_drive(DriveType.HD, APP_DRIVE_LETTER, self.root_dir / APP_DRIVE_LETTER)

        if os_ver != DEFAULT_OS_VER:
            self.run_winetricks(os_ver.value)

    def run_winetricks(self, param: str, quiet: bool = True) -> None:
        wine_env = os.environ.copy()
        for k, v in self.wine_env.items():
            wine_env[k] = v
        cmd = ["winetricks"]
        if quiet:
            cmd.append("-q")
        cmd.append(param)
        run_cmd(cmd, env=wine_env)

    def add_drive(self, drive_type: DriveType, letter: str, target: Path, replace=True, label=None) -> None:
        letter = letter.lower()
        s = f'"{letter}:"="{drive_type.value}"'
        sysreg_path = self.prefix / "system.reg"
        if not str_in_file(sysreg_path, s):
            self.upd_reg({"HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives": [{str(letter + ":"): f"{drive_type.value}"}]})
            while not str_in_file(sysreg_path, s):
                time.sleep(2)
        drive_path = self.prefix / "dosdevices" / str(letter + ":")
        if drive_path.exists():
            if not replace:
                raise ValueError(f"drive {drive_path} already exist")
            if not drive_path.is_symlink():
                raise ValueError(f"drive {drive_path} is not a symlink")
            drive_path.unlink()
        drive_path.symlink_to(os.path.relpath(target, self.prefix / "dosdevices"))
        if label:
            with open(target / ".windows-label", "w", encoding="UTF-8") as f:
                f.write(label)

    def remove_drive(self, letter: str):
        letter = letter.lower()
        s = f'"{letter}:"='
        sysreg_path = self.prefix / "system.reg"
        self.upd_reg({"HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives": [{str(letter + ":"): "-"}]})
        while str_in_file(sysreg_path, s):
            time.sleep(2)
        drive_path = self.prefix / "dosdevices" / str(letter + ":")
        if drive_path.exists():
            if not drive_path.is_symlink():
                raise ValueError(f"drive {drive_path} is not a symlink")
            drive_path.unlink()
        # TODO: rm drive folder?

    def add_cdrom(self, letter: str, target: Path, replace=True, label=None) -> None:
        self.add_drive(DriveType.CDROM, letter, target, replace, label)

    def upd_reg_file(self, reg_file: Path) -> None:
        self.run("regedit", args=str(reg_file))

    def upd_reg(self, reg_dict: Dict[str, List[Dict[str, str]]]) -> None:
        with tempfile.NamedTemporaryFile(mode="w+t", dir=self.root_dir / ".wine" / "drive_c") as f:
            f.write("Windows Registry Editor Version 5.00\n\n")
            for k, v in reg_dict.items():
                f.write(f"[{k}]\n")
                for sv in v:
                    ((subkey, val),) = sv.items()
                    subkey = subkey.replace("\\", "\\\\")
                    if isinstance(val, str):
                        val = val.replace("\\", "\\\\")  # escape
                        val = f'"{val}"'  # quote
                    elif isinstance(val, int):
                        val = f"{val:>08d}"  # pad with zeroes
                        val = f"dword:{val}"
                    elif isinstance(val, PureWindowsPath):
                        val = str(val).replace("\\", "\\\\")
                        val = f'"{val}"'  # quote
                    else:
                        raise ValueError(f"unrecognized val type: {val}")
                    f.write(f'"{subkey}"={val}\n')
                f.write("\n")
            f.flush()
            self.upd_reg_file(Path(f.name))

    def _get_lang(self):
        # export LC_ALL=${lang} produces a warning in run.sh, but it should be ignored, locale does actually change
        if self.lang == "en":
            return "en_US.UTF8"
        elif self.lang == "ru":
            return "ru_RU.UTF8"
        elif self.lang == "pl":
            return "pl_PL.UTF8"
        elif self.lang == "cs":
            return "cs_CS.UTF8"
        elif self.lang == "ja":
            return "ja_JP.UTF8"
        elif self.lang == "sv":
            return "sv_SE.UTF8"
        else:
            raise ValueError(f"unknown language: {self.lang}")

    def gen_run_script(
        self,
        app_exec: str,
        pre_run: List[str] = None,
        work_dir: str = str(APP_DIR),
        chdir: bool = True,
    ) -> Path:
        if pre_run is None:
            pre_run = []
        output_path = self.root_dir / "run.sh"
        tmpl_params = {
            "app_exec": app_exec,
            "virtual_desktop": self.virtual_desktop.value if self.virtual_desktop else None,
            "pre_run": pre_run,
            "resolution": self.resolution,
            "video_output": VIDEO_OUTPUT,
            "user_gamer": USER_GAMER,
            "work_dir": str(work_dir).replace("\\", "\\\\"),
            "lang": self._get_lang(),
            "chdir": chdir,
        }
        template(CURRENT_DIR / "templates" / "run.sh.tmpl", output_path, params=tmpl_params)
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path

    def run(
        self,
        path: Union[Path, PureWindowsPath, str],
        args: Union[List[str], str] = None,
        virtual_desktop: VirtualDesktopResolution = VirtualDesktopResolution.RES_640_480,
    ) -> None:
        wine_env = os.environ.copy()  # without that wine crashes
        for k, v in self.wine_env.items():
            wine_env[k] = v
        is_path = isinstance(path, (Path, PureWindowsPath))
        work_dir = str(path.parent) if is_path else str(SYSTEM_DRIVE) + "\\"
        exec_file = str(path.name) if is_path else path
        cmd_line = ["wine", "start", "/wait", "/d", work_dir]
        vd = self.virtual_desktop or virtual_desktop
        if vd:
            cmd_line += ["explorer", f"/desktop=yag,{vd.value}"]
        cmd_line += [exec_file]
        if args:
            if not isinstance(args, List):
                args = [args]
            cmd_line += args
        run_cmd(cmd_line, env=wine_env)

    @staticmethod
    @DeprecationWarning
    def get_overrides_env(overrides: Dict[str, str] = None) -> str:
        """
        Output a string of dll overrides usable with WINEDLLOVERRIDES
        See: https://wiki.winehq.org/Wine_User%27s_Guide#WINEDLLOVERRIDES.3DDLL_Overrides
        """
        if not overrides:
            return ""
        override_buckets = OrderedDict([("n,b", []), ("b,n", []), ("b", []), ("n", []), ("d", []), ("", [])])
        for dll, value in overrides.items():
            if not value:
                value = ""
            value = value.replace(" ", "")
            value = value.replace("builtin", "b")
            value = value.replace("native", "n")
            value = value.replace("disabled", "")
            try:
                override_buckets[value].append(dll)
            except KeyError:
                print(f"error: invalid override value {value}")
                continue

        override_strings = []
        for value, dlls in override_buckets.items():
            if not dlls:
                continue
            override_strings.append(f"{','.join(sorted(dlls))}={value}")
        return ";".join(override_strings)

    @DeprecationWarning
    def init_wine_prefix(self, env: dict, install_gecko: bool = False, install_mono: bool = False) -> None:
        dll_overrides = {}
        if not install_gecko:
            dll_overrides["mshtml"] = "d"
        if not install_mono:
            dll_overrides["mscoree"] = "d"
        env["WINEDLLOVERRIDES"] = self.get_overrides_env(dll_overrides)
        run_cmd(["wineboot"], env=env)
        # now wait in loop till creation is finished
        system_reg_path = Path(self.prefix) / "system.reg"
        for loop_index in range(50):
            if system_reg_path.exists():
                break
            if loop_index == 20:
                print("warn: wine prefix creation is taking longer than expected...")
            time.sleep(0.25)
        if not system_reg_path.exists():
            print("error: no system.reg found after prefix creation. Prefix might be invalid")
