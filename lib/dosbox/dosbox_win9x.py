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
    Union,
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
from lib.dosbox.dosbox import DosBox
from lib.dosbox.dosbox_conf import (
    DosBoxConf,
    DosBoxFlavor,
    DosBoxMod,
)
from lib.dosbox.misc import (
    DosCmdExec,
    DosMountPointHDD,
)
from lib.utils import copy as cp
from lib.utils import (
    rm,
    template,
)

X_DRIVE_LETTER = "X"
X_DRIVE_DIR = PureWindowsPath("X:\\")

LCOPY_CMD = "LCOPY"
LCOPY_CMD_OPTIONS = ["/Y", "/R", "/A", "/V", "/B", "/C", "/S", "/D"]

XCOPY_CMD = "XCOPY"
XCOPY_CMD_OPTIONS = ["/I", "/E", "/Y", "/H", "/R"]

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

        # x-drive is used as a gate to pass files from the host into the DosBox image drives
        self.x_drive = self.root_dir / X_DRIVE_LETTER
        self.x_drive.mkdir(exist_ok=False)
        self.mount(DosMountPointHDD(X_DRIVE_LETTER, self.x_drive))

        if (
            self.app_descr.app_reqs.screen_width != BASE_SCREEN_WIDTH
            or self.app_descr.app_reqs.color_bits != BASE_COLOR_BITS
        ):
            self.set_display_params(
                self.app_descr.app_reqs.screen_width,
                self.app_descr.app_reqs.screen_height,
                self.app_descr.app_reqs.color_bits,
            )

    def __del__(self):
        if self.x_drive.is_dir():
            self.umount(X_DRIVE_LETTER)
            rm(self.x_drive)
        self.gen_conf()  # regenerating config as per current state

    def regedit(self, reg_dict: Dict[str, List[Dict[str, str]]]) -> None:
        with tempfile.NamedTemporaryFile(mode="w+t", dir=self.x_drive, newline="\r\n") as f:
            f.write("REGEDIT4\n\n")
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

    def copy(self, src: Union[Path, List[Path], PureWindowsPath, List[PureWindowsPath]], dst: PureWindowsPath) -> None:
        """Copies files from source host path (Path) or image drive (PureWindowPath) into another image drive mounted
        into the dosbox instance.

        LCOPY options:
            /Y: turn off prompting
            /R: overwrite existing read-only files
            /A: copy hidden files
            /V: do not use extended memory (mandatory for dosbox-x)
            /B: do not abort operation by pressing any key
            /C: disable cache
            /S: copy subdirectories
            /D: do not create subdirectories when recursing (/S)

        TODO: only LCOPY preserves LFNs, but it fails to copy data from mounted dirs, so we have to use XCOPY to copy
        from X drive.
        TODO: directories copy doesn't work, e.g. "LCOPY D1 D2" will produce an empty /D2/D1 directory.
        You need to create /D2/D1 beforehand and use "LCOPY D1/* D2/D1" syntax instead.
        """
        if not isinstance(src, List):
            src = [src]
        cmds = []
        # we might want to remove /D in certain cases:
        # - when copying SRC/* into DST we want to preserve subdirectories with all files inside (by removing /D)
        # - when copying a single file (SRC/file.ext) into DST, we need to keep /D, otherwise
        # LCOPY will recreate the whole structure of SRC at DST (bug: https://github.com/oglueck/lfntools/issues/1)
        # another bug has been discovered: when using /S and trying to copy a single file, LCOPY will also try to
        # copy all subdirs on the src drive into destination and /D won't help. So we need to remove /S for files.
        lcopy_cmd_options = LCOPY_CMD_OPTIONS.copy()
        if len(src) > 1 or "*" in str(src[0]):
            # when there are multiple sources, destination is always a folder.
            # also handle case when there is only one source and it contains "*"
            # we need to created it for safety
            self.md(dst)
        for s in src:
            if "/D" not in lcopy_cmd_options:
                lcopy_cmd_options.append("/D")
            # removing /D for "*" copies (when src contains *, dest is always a folder)
            if "*" in str(s):
                lcopy_cmd_options.remove("/D")
            if "/S" not in lcopy_cmd_options:
                lcopy_cmd_options.append("/S")
            # removing /S for files due to a bug (see above)
            if "." in str(s):
                lcopy_cmd_options.remove("/S")
            if isinstance(s, Path):
                # copy from host into dosbox
                cp(s, self.x_drive)
                # warning: LFNs are not supported by XCOPY, and LCOPY can't work with mounted folders, only images
                cmds.append(DosCmdExec(XCOPY_CMD, [X_DRIVE_DIR / s.name, dst, *XCOPY_CMD_OPTIONS]))
            elif isinstance(s, PureWindowsPath):
                # intra-dosbox copy
                cmds.append(DosCmdExec(LCOPY_CMD, [s, dst, *lcopy_cmd_options]))
            else:
                raise ValueError(f"unrecognized copy param type: {s}")
        self._run(cmds)

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
