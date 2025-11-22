import stat
from pathlib import (
    Path,
    PureWindowsPath,
)
from typing import (
    List,
    Protocol,
    TypeVar,
    Union,
)

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DRIVE_LETTER,
    CONF_NAME,
    SYSTEM_DRIVE_LETTER,
)
from lib.dosbox.dosbox_conf import (
    BASE_MOUSE_SENSITIVITY,
    DosBoxConf,
    DosBoxFlavor,
    DosBoxMod,
)
from lib.dosbox.misc import (
    DosCmdExec,
    DosMountPoint,
    DosMountPointHDD,
)
from lib.utils import copy as cp
from lib.utils import (
    rm,
    run_cmd,
    template,
)

X_DRIVE_LETTER = "X"
X_DRIVE_DIR = PureWindowsPath("X:\\")

LCOPY_CMD = "LCOPY"
LCOPY_CMD_OPTIONS = ["/Y", "/R", "/A", "/V", "/B", "/C", "/S", "/D"]

XCOPY_CMD = "XCOPY"
XCOPY_CMD_OPTIONS = ["/I", "/E", "/Y", "/H", "/R"]
# TODO: option "/I" should be there but it glitches: when trying to overwrite a single existing
# file, it thinks dest is a dir and fails to copy

AUTOLOCK_MOUSE_SENSITIVITY = 50
MIN_APP_DRIVE_SIZE = 5
CURRENT_DIR = Path(__file__).resolve().parent

T = TypeVar("T", bound=DosBoxConf)


class DosBox(Protocol[T]):
    def __init__(self, root_dir: Path, conf: DosBoxConf, app_descr: AppDesc) -> None:
        if not root_dir.exists():
            raise ValueError(f"root dir doesn't exist: {root_dir}")
        self.conf: T = conf
        self.root_dir = root_dir
        self.app_descr = app_descr
        self.conf.lang = app_descr.lang
        self.conf.autolock = app_descr.app_reqs.ua.lock_pointer
        self.system_drive = root_dir / SYSTEM_DRIVE_LETTER
        self.app_drive = root_dir / APP_DRIVE_LETTER
        self.templates_dir = CURRENT_DIR / "templates" / self.conf.mod.value / self.conf.flavor.value
        self.files_dir = CURRENT_DIR / "files" / self.conf.mod.value
        self.run_cmds: list[Union[DosCmdExec, str]] | None = (
            None  # TODO: should we optionally accept cmds in the ctor and execute them right away?
        )
        # xorg doesn't support lower than 640, so scaling up
        # leave aspect as false for e.g. Lost Eden, otherwise lower bottom will be cut
        if app_descr.app_reqs.screen_width == 320:
            self.conf.scaler = "normal2x"
            self.conf.aspect = False

        # x-drive is used as a gate to pass files from the host into the DosBox image drives
        self.x_drive = self.root_dir / X_DRIVE_LETTER
        self.x_drive.mkdir(exist_ok=False)
        self.mount(DosMountPointHDD(X_DRIVE_LETTER, self.x_drive))

        self.gen_run_script()

    def __del__(self):
        if self.x_drive.is_dir():
            self.umount(X_DRIVE_LETTER)
            rm(self.x_drive)
        self.gen_conf()  # regenerating config as per current state

    def mount(self, mount_points: Union[DosMountPoint, list[DosMountPoint]] = None):
        if mount_points is None:
            mount_points = []
        return self.conf.mount(mount_points)

    def umount(self, drive_letter: Union[str, list[str]], remove: bool = False) -> None:
        if isinstance(drive_letter, str):
            drive_letter = [drive_letter]
        for dl in drive_letter:
            self.conf.umount(dl, remove)

    def umount_all(self, remove: bool = False, cd_only: bool = False):
        self.conf.umount_all(remove, type)

    def create_hdd_image(self, drive_letter: str, image_size: int):
        self._run(
            DosCmdExec(
                PureWindowsPath("IMGMAKE"),
                [PureWindowsPath(drive_letter), "-t", "hd", "-size", max(image_size, MIN_APP_DRIVE_SIZE)],
            )
        )

    def md(self, path: PureWindowsPath):
        # md in dosbox doesn't support backslashes nor intermediate paths creation
        # so we create intermediate paths in a loop replacing backslashes
        cmds = []
        paths = []
        path_tmp = path
        while len(path_tmp.parts) > 1:
            paths.append(path_tmp.parent)
            path_tmp = path_tmp.parent
        paths.reverse()
        paths = [str(p).replace("/", "\\") for p in paths[1:]]
        paths.append(path)
        for p in paths:
            cmds.append(
                DosCmdExec(
                    PureWindowsPath("MD"),
                    [p],
                )
            )
        self._run(cmds)

    def _run_dosbox(self, dosbox_conf_path: Path) -> None:
        if self.conf.mod == DosBoxMod.X:
            cmd = ["dosbox-x"]
        else:
            # orig, staging etc
            cmd = ["dosbox"]
        cmd += ["-conf", dosbox_conf_path, "-noconsole"]
        run_cmd(cmd, cwd=self.root_dir)

    def _run(
        self,
        cmds=Union[DosCmdExec, list[DosCmdExec], str, list[str]],
        mock=False,
    ):
        """Runs command(s) inside the dos env. For internal use only.
        Create wrapper functions to call _run (see "md" implementation).

        To run command(s) in the flavored env, use the run() method from an appropriate implementation.
        """
        if not isinstance(cmds, list):
            cmds = [cmds]
        # gen conf
        self.run_cmds = []
        for c in cmds:
            if isinstance(c, DosCmdExec):
                for c_ in c.iter():
                    self.run_cmds.append(c_)
            else:
                self.run_cmds.append(c)
        dosbox_conf_path = self.gen_conf()
        if mock:
            return
        self._run_dosbox(dosbox_conf_path)

    def gen_run_script(self) -> Path:
        output_path = self.root_dir / "run.sh"
        tmpl_params = {
            "dosbox_conf": (self.root_dir / "dosbox.conf").relative_to(self.root_dir),
            "autolock": str(self.conf.autolock).lower(),  # for: SDL_VIDEO_X11_DGAMOUSE=0
        }
        template(
            self.templates_dir / "run.sh.tmpl",
            output_path,
            params=tmpl_params,
        )
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path

    def gen_conf(self) -> Path:
        """Generate dosbox.conf in the root_dir / dosbox.conf

        Return: path to the generated config
        """

        if self.conf.mod == DosBoxMod.X:
            # copy kbd mapping file: redefined host key from F12 to Ctrl and Swap CD operation from D to F4,
            # so it's Ctrl+F4 as in the classic DosBox
            cp(self.files_dir / "mapper-dosbox-x.map", self.root_dir)

        autoexec_cmds = self.conf.gen_mount_cmds(self.root_dir)
        for c in self.run_cmds:
            autoexec_cmds.append(c)
        autoexec_cmds.append("EXIT")
        default_sensitivity = AUTOLOCK_MOUSE_SENSITIVITY if self.conf.autolock else BASE_MOUSE_SENSITIVITY
        tmpl_params = {
            "autolock": str(self.conf.autolock).lower(),
            "autoexec": autoexec_cmds,
            "memsize": self.conf.memsize,
            "scaler": self.conf.scaler,
            "aspect": self.conf.aspect,
            "cdrom_insertion_delay": self.conf.cdrom_insertion_delay,
            "cycles": self.conf.cycles,
            "fullscreen": str(self.conf.fullscreen).lower(),
            "sensitivity": self.conf.sensitivity or default_sensitivity,
            "gus": self.conf.gus,
        }
        dest_path = self.root_dir / CONF_NAME
        template(
            self.templates_dir / f"{CONF_NAME}.tmpl",
            dest_path,
            params=tmpl_params,
        )
        return dest_path

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

        if len(src) > 1 or "*" in str(src[0]):
            # when there are multiple sources, destination is always a folder.
            # also handle case when there is only one source and it contains "*"
            # we need to create it for safety
            self.md(dst)
        for s in src:
            if isinstance(s, Path):
                # copy from host into dosbox
                cp(s, self.x_drive)
                # warning: LFNs are not supported by XCOPY, and LCOPY can't work with mounted folders, only images
                cmds.append(DosCmdExec(XCOPY_CMD, [X_DRIVE_DIR / s.name, dst, *XCOPY_CMD_OPTIONS]))
            elif isinstance(s, PureWindowsPath):
                # intra-dosbox copy
                if self.conf.flavor == DosBoxFlavor.DOS:
                    # using XCOPY for pure DOS as LCOPY is not available there
                    cmds.append(DosCmdExec(XCOPY_CMD, [s, dst, *XCOPY_CMD_OPTIONS]))
                else:
                    # we might want to remove /D in certain cases:
                    # - when copying SRC/* into DST we want to preserve subdirectories with all files inside
                    # (by removing /D)
                    # - when copying a single file (SRC/file.ext) into DST, we need to keep /D, otherwise
                    # LCOPY will recreate the whole structure of SRC at DST
                    # (bug: https://github.com/oglueck/lfntools/issues/1)
                    # another bug has been discovered: when using /S and trying to copy a single file, LCOPY will also
                    # try to copy all subdirs on the src drive into destination and /D won't help.
                    # So we need to remove /S for files.
                    lcopy_cmd_options = LCOPY_CMD_OPTIONS.copy()
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
                    cmds.append(DosCmdExec(LCOPY_CMD, [s, dst, *lcopy_cmd_options]))
            else:
                raise ValueError(f"unrecognized copy param type: {s}")
        self._run(cmds)
