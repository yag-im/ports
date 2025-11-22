import tempfile
from dataclasses import (
    dataclass,
    field,
)
from pathlib import (
    Path,
    PureWindowsPath,
)
from typing import (
    Any,
    Dict,
    List,
)

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DRIVE_LETTER,
    DEFAULT_APP_DRIVE_SIZE,
    FIRST_CD_DRIVE,
    RUNNERS_BUNDLES_BASE_DIR,
    SYSTEM_DRIVE,
    SYSTEM_DRIVE_LETTER,
)
from lib.dosbox.dosbox import (
    X_DRIVE_LETTER,
    DosBox,
)
from lib.dosbox.dosbox_conf import (
    DosBoxConf,
    DosBoxFlavor,
    DosBoxMod,
)
from lib.dosbox.misc import (
    DosCmdExec,
    DosMountPointHDD,
)
from lib.unpack import unpack_archive
from lib.utils import copy as cp
from lib.utils import (
    template,
)

BASE_SCREEN_WIDTH = 640
BASE_SCREEN_HEIGHT = 480
BASE_COLOR_BITS = 16


@dataclass
class DosBoxWin9xConf(DosBoxConf):
    app_drive_size: int = DEFAULT_APP_DRIVE_SIZE
    mod: DosBoxMod = field(default=DosBoxMod.X)
    flavor: DosBoxFlavor = field(default=DosBoxFlavor.WIN95OSR25)


class DosBoxWin9x(DosBox[DosBoxWin9xConf]):
    def __init__(self, root_dir: Path, app_descr: AppDesc, conf: DosBoxWin9xConf = DosBoxWin9xConf()) -> None:
        super().__init__(root_dir, conf, app_descr)

        # copy bundled system drive image: bundles/dosbox-x/win9x/C -> root_dir/C
        cp(
            RUNNERS_BUNDLES_BASE_DIR
            / self.conf.mod.value
            / f"{self.conf.flavor.value}-{self.conf.lang}"
            / SYSTEM_DRIVE_LETTER,
            self.root_dir,
        )
        # drive D can't be a folder as dosbox-x doesn't support persistent mounted folders in win9x env, only images
        self.create_hdd_image(APP_DRIVE_LETTER, self.conf.app_drive_size)
        self.mount(
            [
                DosMountPointHDD(SYSTEM_DRIVE_LETTER, self.system_drive),
                DosMountPointHDD(APP_DRIVE_LETTER, self.app_drive),
            ]
        )

        if (
            self.app_descr.app_reqs.screen_width != BASE_SCREEN_WIDTH
            or self.app_descr.app_reqs.color_bits != BASE_COLOR_BITS
        ):
            self.set_display_params(
                self.app_descr.app_reqs.screen_width,
                self.app_descr.app_reqs.screen_height,
                self.app_descr.app_reqs.color_bits,
            )

    def regedit(self, reg_dict: Dict[str, List[Dict[str, str]]]) -> None:
        with tempfile.NamedTemporaryFile(mode="w+t", dir=self.x_drive, newline="\r\n") as f:
            f.write("REGEDIT4\n\n")
            for k, v in reg_dict.items():
                norm_k = k.replace("/", "\\")
                f.write(f"[{norm_k}]\n")
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
            # drive X becomes drive E (first CD drive) after booting into Win9x :(
            self.run("C:\\WINDOWS\\REGEDIT.EXE", args=["/s", FIRST_CD_DRIVE / Path(f.name).name], umount_x=False)

    def set_display_params(self, screen_width: int, screen_height, color_bits: int):
        self.regedit(
            {
                "HKEY_CURRENT_CONFIG\\Display\\Settings": [
                    {"Resolution": f"{screen_width},{screen_height}"},
                    {"BitsPerPixel": str(color_bits)},
                ]
            }
        )

    def extract(self, src: Path, dst: PureWindowsPath, files: List[str] = None) -> None:
        """Extracts files from source host path into the dosbox' mounted image drive."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            unpack_archive(src, tmp_path, extract_files=files)
            # copy creates missing dst directory automatically
            self.copy(tmp_path, dst)

    def run(
        self, path: PureWindowsPath, args: List[Any] = None, mock=False, runexit=True, umount_x=True, workdir=None
    ) -> None:
        """Runs existing app in the Win9x-flavored env (runs after Win9x is booted inside the DosBox instance).

        You'll need to copy a file beforehand if it doesn't exist in the flavored env.
        A new Shell is being set in the SYSTEM.INI.

        mock: only propagate a new SYSTEM.INI and generate a dosbox.conf
        """
        if args is None:
            args = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            shell_cmds = []
            if runexit:
                shell_cmds.append("RUNEXIT.EXE")
            if workdir:
                shell_cmds.append(f'/C:"{workdir}"')
            shell_cmds.append(f'"{path}"')
            if args:
                shell_cmds.append(" ".join([str(a) for a in args]))
            tmp_file_path = Path(tmp_dir) / "SYSTEM.INI"
            template(
                self.templates_dir / "system.ini.tmpl",
                tmp_file_path,
                params={
                    "shell": " ".join([str(cmd) for cmd in shell_cmds]),
                },
                newline="\r\n",
            )
            self.copy(tmp_file_path, SYSTEM_DRIVE / "WINDOWS")

        # X drive normally should not appear in the Win9x env
        # exceptions: regedit.exe will need drive X (appears as drive E in Win9x)
        if umount_x:
            self.umount(X_DRIVE_LETTER)
        self._run(DosCmdExec("BOOT", [f"{SYSTEM_DRIVE_LETTER}:"]), mock=mock)
        if umount_x:
            self.mount(DosMountPointHDD(X_DRIVE_LETTER, self.x_drive))
