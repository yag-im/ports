import os
import stat
import tempfile
from abc import (
    abstractmethod,
)
from dataclasses import (
    dataclass,
)
from enum import StrEnum
from pathlib import (
    Path,
    PureWindowsPath,
)
from shutil import move
from typing import (
    Any,
    Protocol,
    TypeVar,
)

from lib.app_desc import AppDesc
from lib.const import (
    APP_DRIVE_LETTER,
    RUNNERS_BUNDLES_BASE_DIR,
    SYSTEM_DRIVE_LETTER,
)
from lib.guestfs import copy as guestfs_copy
from lib.guestfs import replace_string_in_file as guestfs_replace_string_in_file
from lib.guestfs import rm as guestfs_rm
from lib.qemu.const import (
    APP_DRIVE,
)
from lib.utils import copy as cp
from lib.utils import (
    is_iso_image,
    rm,
    run_cmd,
    template,
)

CURRENT_DIR = Path(__file__).resolve().parent

BASE_LANG = "en"
KNOWN_LANG = {BASE_LANG, "ru"}

BASE_FULLSCREEN_ENABLED = True


class QemuFlavor(StrEnum):
    WINXPSP3 = "winxpsp3"
    WIN98SE = "win98se"


@dataclass
class QemuConf:
    flavor: QemuFlavor
    # Avoid using `-cpu host`. Because the cloud CPU differs from the local dev CPU,
    # OS will detect a new processor and will raise a "New hardware has been found" wizard during the first boot.
    cpu: str
    memory: int
    color_bits: int
    screen_width: int
    audio_device: str
    reg_file_encoding: str
    pointer_device: str
    _lang: str = BASE_LANG
    # some games require CD swaps and therefore a switch to qemu monitor;
    # after returning from monitor, mouse grab may not work in a full-screen mode;
    fullscreen: bool = BASE_FULLSCREEN_ENABLED

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, new_value):
        # only BASE_LANG and "ru" versions are supported
        self._lang = new_value if new_value in KNOWN_LANG else BASE_LANG


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


T = TypeVar("T", bound=QemuConf)


class Qemu((Protocol[T])):
    def __init__(
        self,
        root_dir: Path,
        app_descr: AppDesc,
        conf: QemuConf,
    ) -> None:
        self.root_dir = root_dir
        self.app_descr = app_descr
        self.conf = conf
        self.conf.lang = app_descr.lang
        self.mount_points: list[QemuMountPoint] = []
        self.templates_dir = CURRENT_DIR / "templates" / self.conf.flavor.value
        self.conf.pointer_device = None if self.app_descr.app_reqs.ua.lock_pointer else "tablet"

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
            index=1,
            media="disk",
            letter=APP_DRIVE_LETTER,
            image_format="qcow2",
        )

        if (
            self.app_descr.app_reqs.screen_width != self.conf.screen_width
            or self.app_descr.app_reqs.color_bits != self.conf.color_bits
        ):
            self.set_display_params(
                self.app_descr.app_reqs.screen_width,
                self.app_descr.app_reqs.screen_height,
                self.app_descr.app_reqs.color_bits,
            )

    @abstractmethod
    def run_exec(
        self,
        exec_path: PureWindowsPath | str,
        do_exit: bool = True,
        mock: bool = False,
        work_dir: PureWindowsPath | None = None,  # runexit script dir for winxp
        args: list[Any] | None = None,
    ) -> None:
        pass

    @abstractmethod
    def set_display_params(self, screen_width: int, screen_height: int, color_bits: int) -> None:
        pass

    def umount(self, drive_letter: str, remove: bool = False) -> None:
        mp = next((x for x in self.mount_points if x.letter == drive_letter), None)
        if mp:
            self.mount_points.remove(mp)
        if remove:
            rm(mp.image_path)

    def mount(
        self,
        image_path: Path,
        interface: str | None = "ide",
        index: int | None = None,
        media: str | None = None,
        letter: str | None = None,
        image_format: str | None = None,
    ):
        # TODO: fails to mount another drive to already mounted letter requiring an explicit umount. Bug?
        if media == "cdrom":
            if not is_iso_image(image_path):
                # qemu supports only iso cdrom images
                with tempfile.TemporaryDirectory() as td:
                    tmp_iso_image = Path(td) / "tmp.iso"
                    run_cmd(["iat", "-i", image_path, "-o", tmp_iso_image, "--iso"])
                    move(tmp_iso_image, image_path)
        index = len(self.mount_points) if index is None else index
        letter = letter or chr(ord("A")) + index + 2
        self.mount_points.append(
            QemuMountPoint(
                image_path=image_path, interface=interface, index=index, media=media, letter=letter, format=image_format
            )
        )

    def _run_qemu(self) -> None:
        cmd = ["qemu-system-x86_64", "-nodefaults"]
        for mp in self.mount_points:
            cmd.append("-drive")
            cmd.append(mp.qemu_drive_mount_option_relative_to(self.root_dir))
        cmd += ["-enable-kvm", "-cpu", str(self.conf.cpu), "-m", str(self.conf.memory), "-display", "sdl"]
        # order of devices is important even with -nodefaults, so can't just append at the end
        if self.conf.flavor == QemuFlavor.WINXPSP3:
            cmd += ["-vga", "virtio"]
        elif self.conf.flavor == QemuFlavor.WIN98SE:
            cmd += ["-device", "VGA"]
        cmd += [
            "-audiodev",
            "pa,id=pa1",
            "-device",
            f"{self.conf.audio_device},audiodev=pa1",
            "-monitor",
            "vc",
        ]
        if self.conf.pointer_device:
            cmd += [
                "-usbdevice",
                f"{self.conf.pointer_device}",
            ]

        run_cmd(cmd, cwd=self.root_dir)

    # check implementations for a run script inside OS
    def gen_run_script(self, exec_path: PureWindowsPath) -> Path:
        output_path = self.root_dir / "run.sh"
        display = "sdl,full-screen=on,gl=on" if self.conf.fullscreen else "gtk,show-menubar=off,full-screen=off,gl=on"
        tmpl_params = {
            "cpu": self.conf.cpu,
            "memory": self.conf.memory,
            "mounts": " ".join(
                str("-drive " + mp.qemu_drive_mount_option_relative_to(self.root_dir)) for mp in self.mount_points
            ),
            "display": display,
            "audiodev": self.conf.audio_device,
            "flavor": self.conf.flavor.name,
            "pointerdev": self.conf.pointer_device,
        }
        template(
            self.templates_dir / "run.sh.tmpl",
            output_path,
            params=tmpl_params,
        )
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path

    def rm(self, path: PureWindowsPath):
        img_path = self._get_mounted_image_path(path.drive.rstrip(":").upper())
        file_path = "/" + str(path.relative_to(path.anchor)).replace("\\", "/")
        print(f"removing file: '{file_path}' from image drive: '{img_path}'")
        guestfs_rm(img_path, file_path)

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

        if is_guest_path(dest):
            pdest = PureWindowsPath(dest)
            dst_img_path = self._get_mounted_image_path(pdest.drive.rstrip(":").upper())
            dst_file_path = Path("/" + str(pdest.relative_to(pdest.anchor)).replace("\\", "/"))
        else:
            dst_img_path, dst_file_path = None, Path(dest)

        guestfs_copy(src_img_path, src_file_path, dst_img_path, dst_file_path)

    def replace_string_in_file(self, guest_path: PureWindowsPath, old, new):
        """
        Replace a string in a file inside a guest filesystem using libguestfs.

        :param guest_path: Path to the file inside the guest.
        :param old: The string to be replaced.
        :param new: The replacement string.
        :param filesystem: Device inside guest to mount (default: "/dev/sda1").
        """

        src_img_path = self._get_mounted_image_path(guest_path.drive.rstrip(":").upper())
        src_file_path = "/" + str(guest_path.relative_to(guest_path.anchor)).replace("\\", "/")
        guestfs_replace_string_in_file(src_img_path, src_file_path, old, new)
        print(f"Replaced '{old}' with '{new}' in {guest_path}")

    def upd_reg(self, reg_dict: dict[str, list[dict[str, str]]]) -> None:
        def _norm_subkey(subkey):
            subkey = subkey.replace("\\", "\\\\")
            if subkey == "@":
                return subkey
            else:
                return f'"{subkey}"'

        with tempfile.NamedTemporaryFile(
            mode="w+t", newline="\r\n", encoding=self.conf.reg_file_encoding, suffix=".reg"
        ) as f:
            if self.conf.flavor == QemuFlavor.WINXPSP3:
                f.write("Windows Registry Editor Version 5.00\n\n")
            elif self.conf.flavor == QemuFlavor.WIN98SE:
                f.write("REGEDIT4\n\n")
            for k, v in reg_dict.items():
                norm_k = k.replace("/", "\\")
                f.write(f"[{norm_k}]\n")
                for sv in v:
                    ((subkey, val),) = sv.items()
                    if isinstance(val, str):
                        val = val.replace("\\", "\\\\")  # escape
                        val = f'"{val}"'  # quote
                    elif isinstance(val, int):
                        val = f"{val:>08d}"  # pad with zeroes
                        val = f"dword:{val}"
                    elif isinstance(val, PureWindowsPath):
                        val = str(val).replace("\\", "\\\\")
                        val = f'"{val}"'  # quote
                    elif isinstance(val, (bytes, bytearray)):
                        val = "hex:" + ",".join(f"{b:02x}" for b in val)
                    else:
                        raise ValueError(f"unrecognized val type: {val}")
                    f.write(f"{_norm_subkey(subkey)}={val}\n")
                f.write("\n")
            f.flush()

            self.copy(
                os.path.abspath(f.name),
                APP_DRIVE,
            )

            self.run_exec("regedit", args=["/s", APP_DRIVE / os.path.basename(f.name)])

            self.rm(
                APP_DRIVE / os.path.basename(f.name),
            )
