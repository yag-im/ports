import stat
from pathlib import (
    Path,
    PureWindowsPath,
)
from typing import (
    List,
    Optional,
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
    DosBoxMod,
)
from lib.dosbox.misc import (
    DosCmdExec,
    DosMountPoint,
)
from lib.utils import (
    run_cmd,
    template,
)

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
        self.run_cmds: Optional[List[DosCmdExec]] = (
            None  # TODO: should we optionally accept cmds in the ctor and execute them right away?
        )
        # xorg doesn't support lower than 640, so scaling up
        # leave aspect as false for e.g. Lost Eden, otherwise lower bottom will be cut
        if app_descr.app_reqs.screen_width == 320:
            self.conf.scaler = "normal2x"
            self.conf.aspect = False
        self.gen_run_script()

    def mount(self, mount_points: Union[DosMountPoint, List[DosMountPoint]] = None):
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

    def create_hdd_image(self, drive_letter: chr, image_size: int):
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
        cmds=Union[DosCmdExec, List[DosCmdExec]],
        mock=False,
    ):
        """Runs command(s) inside the dos env. For internal use only.
        Create wrapper functions to call _run (see "md" implementation).

        To run command(s) in the flavored env, use the run() method from an appropriate implementation.
        """
        if not isinstance(cmds, List):
            cmds = [cmds]
        # gen conf
        self.run_cmds = []
        c: DosCmdExec
        for c in cmds:
            for c_ in c.iter():
                self.run_cmds.append(c_)
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
        }
        dest_path = self.root_dir / CONF_NAME
        template(
            self.templates_dir / f"{CONF_NAME}.tmpl",
            dest_path,
            params=tmpl_params,
        )
        return dest_path
