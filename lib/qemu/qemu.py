import stat
import tempfile
from dataclasses import (
    dataclass,
    field,
)
from enum import StrEnum
from pathlib import (
    Path,
    PureWindowsPath,
)
from shutil import move
from typing import Union

from lib.app_desc import AppDesc
from lib.const import (
    APP_DRIVE_LETTER,
    RUNNERS_BUNDLES_BASE_DIR,
    SYSTEM_DRIVE_LETTER,
)
from lib.guestfs import copy as guestfs_copy
from lib.utils import copy as cp
from lib.utils import (
    is_iso_image,
    run_cmd,
    template,
)

CURRENT_DIR = Path(__file__).resolve().parent
BASE_LANG = "en"


class QemuFlavor(StrEnum):
    WINXPSP3 = "winxpsp3"


@dataclass
class QemuConf:
    flavor: QemuFlavor = field(default=QemuFlavor.WINXPSP3)
    memory: int = 1024
    # Avoid using `-cpu host`. Because the cloud CPU differs from the local dev CPU,
    # OS will detect a new processor and will raise a "New hardware has been found" wizard during the first boot.
    cpu: str = "Skylake-Server,model-id=Intel"
    _lang = BASE_LANG

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, new_value):
        # only BASE_LANG and "ru" versions are supported
        self._lang = new_value if new_value in {BASE_LANG, "ru"} else BASE_LANG


@dataclass
class QemuMountPoint:
    image_path: Path
    interface: str
    index: int
    media: str
    letter: str
    format: str | None = None

    def qemu_drive_mount_option_relative_to(self, p_base: Path | None = None):
        if p_base:
            rel_path = self.image_path.relative_to(p_base)
        else:
            rel_path = self.image_path
        res = f"file={rel_path},if={self.interface},index={self.index},media={self.media}"
        if self.format:
            res += f",format={self.format}"
        return res


class Qemu:
    def __init__(self, root_dir: Path, app_descr: AppDesc, conf: QemuConf = QemuConf()) -> None:
        self.root_dir = root_dir
        self.app_descr = app_descr
        self.conf = conf
        self.conf.lang = app_descr.lang
        self.mount_points: list[QemuMountPoint] = []
        self.templates_dir = CURRENT_DIR / "templates" / self.conf.flavor.value

        # copy bundled system drive image: bundles/qemu/winxp-$LANG/C -> root_dir/C
        cp(
            RUNNERS_BUNDLES_BASE_DIR / "qemu" / f"{self.conf.flavor.value}-{self.conf.lang}" / SYSTEM_DRIVE_LETTER,
            self.root_dir,
        )
        self.mount(
            image_path=self.root_dir / SYSTEM_DRIVE_LETTER,
            index=0,
            media="disk",
            letter=SYSTEM_DRIVE_LETTER,
            image_format="qcow2",
        )

        # copy bundled apps drive image: bundles/qemu/winxp-$LANG/D -> root_dir/D
        cp(
            RUNNERS_BUNDLES_BASE_DIR / "qemu" / f"{self.conf.flavor.value}-{self.conf.lang}" / APP_DRIVE_LETTER,
            self.root_dir,
        )
        self.mount(
            image_path=self.root_dir / APP_DRIVE_LETTER,
            index=2,
            media="disk",
            letter=APP_DRIVE_LETTER,
            image_format="qcow2",
        )

    def mount(
        self,
        image_path: Path,
        interface: str | None = "ide",
        index: int | None = None,
        media: str | None = None,
        letter: str | None = None,
        image_format: str | None = None,
    ):
        if media == "cdrom":
            if not is_iso_image(image_path):
                # qemu supports only iso cdrom images
                with tempfile.TemporaryDirectory() as td:
                    tmp_iso_image = Path(td) / "tmp.iso"
                    run_cmd(["iat", image_path, tmp_iso_image])
                    move(tmp_iso_image, image_path)
        index = len(self.mount_points) + 1 if index is None else index
        letter = letter or chr(ord("A")) + index + 1
        self.mount_points.append(
            QemuMountPoint(
                image_path=image_path, interface=interface, index=index, media=media, letter=letter, format=image_format
            )
        )

    def _run_qemu(self) -> None:
        cmd = ["qemu-system-x86_64"]
        for mp in self.mount_points:
            cmd.append("-drive")
            cmd.append(mp.qemu_drive_mount_option_relative_to(self.root_dir))
        cmd += [
            "-enable-kvm",
            "-cpu",
            str(self.conf.cpu),
            "-m",
            str(self.conf.memory),
            "-net",
            "nic,model=rtl8139",
            "-net",
            "user",
            "-usbdevice",
            "tablet",
            "-vga",
            "virtio",
            "-display",
            "sdl",
            "-audiodev",
            "pa,id=pa1",
            "-device",
            "AC97,audiodev=pa1",
        ]
        run_cmd(cmd, cwd=self.root_dir)

    def _run(
        self,
        cmd: Union[str, list[str]],
        do_exit: bool = True,
        mock: bool = False,
        runexit_script_dir: PureWindowsPath | None = None,
    ) -> None:
        if isinstance(cmd, str):
            cmd = [cmd]
        with tempfile.TemporaryDirectory() as td:
            tmp_runexit_bat = Path(td) / "RUNEXIT.BAT"
            tmpl_params = {"cmd": "\r\n".join([str(c) for c in cmd]), "exit": do_exit}
            template(
                self.templates_dir / "RUNEXIT.BAT.tmpl",
                tmp_runexit_bat,
                params=tmpl_params,
                newline="\r\n",
            )
            if runexit_script_dir:
                dest_path = runexit_script_dir
            else:
                dest_path = "C:\\Documents and Settings\\gamer\\Start Menu\\Programs\\Startup"
                if self.conf.lang == "ru":
                    dest_path = "C:\\Documents and Settings\\gamer\\Главное меню\\Программы\\Автозагрузка"
            self.copy(
                tmp_runexit_bat,
                PureWindowsPath(dest_path),
            )
        if not mock:
            self._run_qemu()

    def run(
        self,
        path: PureWindowsPath,
        do_exit: bool = True,
        mock: bool = False,
        runexit_script_dir: PureWindowsPath | None = None,
    ) -> None:
        cmd = f'start /wait "" /D "{str(path.parent)}" "{path}"'
        return self._run(cmd, do_exit=do_exit, mock=mock, runexit_script_dir=runexit_script_dir)

    def gen_run_script(self, exec_path: PureWindowsPath) -> Path:
        self.run(
            exec_path, mock=True, runexit_script_dir=PureWindowsPath("D:\\APP")
        )  # this value goes into registry so no backslashes in a path
        self._run(
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon" '
            "/v Shell /t REG_SZ "
            '/d "D:\\APP\\RUNEXIT.BAT" /f'
        )
        output_path = self.root_dir / "run.sh"
        tmpl_params = {
            "cpu": self.conf.cpu,
            "memory": self.conf.memory,
            "mounts": " ".join(
                str("-drive " + mp.qemu_drive_mount_option_relative_to(self.root_dir)) for mp in self.mount_points
            ),
        }
        template(
            self.templates_dir / "run.sh.tmpl",
            output_path,
            params=tmpl_params,
        )
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)

        return output_path

    def _get_mounted_image_path(self, letter: str) -> Path | None:
        for mp in self.mount_points:
            if mp.letter == letter.upper():
                return mp.image_path
        return None

    def copy(self, src: Path, dest: Path):
        def is_guest_path(path: str) -> bool:
            p = PureWindowsPath(path)
            return p.drive != ""

        if is_guest_path(src):
            psrc = PureWindowsPath(src)
            src_img_path = self._get_mounted_image_path(psrc.drive.rstrip(":").upper())
            # guestfs wants forward slashes, no drive letter
            src_file_path = Path("/" + str(psrc.relative_to(psrc.anchor)).replace("\\", "/"))
        else:
            src_img_path, src_file_path = None, Path(src)

        # Destination
        if is_guest_path(dest):
            pdest = PureWindowsPath(dest)
            dst_img_path = self._get_mounted_image_path(pdest.drive.rstrip(":").upper())
            dst_file_path = Path("/" + str(pdest.relative_to(pdest.anchor)).replace("\\", "/"))
        else:
            dst_img_path, dst_file_path = None, Path(dest)

        guestfs_copy(src_img_path, src_file_path, dst_img_path, dst_file_path)
