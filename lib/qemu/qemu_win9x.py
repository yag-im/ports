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
)

from lib.app_desc import AppDesc
from lib.qemu.const import SYSTEM_DRIVE
from lib.qemu.qemu import (
    Qemu,
    QemuConf,
    QemuFlavor,
)

BASE_CPU = "pentium2-v1"
BASE_MEMORY = 256

BASE_SCREEN_WIDTH = 640
BASE_COLOR_BITS = 16
BASE_AUDIO_DEVICE = "AC97"


@dataclass
class QemuWin9xConf(QemuConf):
    flavor: QemuFlavor = field(default=QemuFlavor.WIN98SE)
    cpu: str = BASE_CPU
    memory: int = BASE_MEMORY
    color_bits: int = BASE_COLOR_BITS
    screen_width: int = BASE_SCREEN_WIDTH
    audio_device: str = BASE_AUDIO_DEVICE
    reg_file_encoding: str = "utf-8"


class QemuWin9x(Qemu[QemuWin9xConf]):
    def __init__(self, root_dir: Path, app_descr: AppDesc, conf: QemuWin9xConf = QemuWin9xConf()) -> None:
        super().__init__(root_dir, app_descr, conf)

    def set_display_params(self, screen_width: int, screen_height: int, color_bits: int):
        self.upd_reg(
            {
                "HKEY_CURRENT_CONFIG\\Display\\Settings": [
                    {"Resolution": f"{screen_width},{screen_height}"},
                    {"BitsPerPixel": str(color_bits)},
                ]
            }
        )

    def run_on_startup(
        self,
        exec_path: str,
        do_exit: bool = True,
        mock: bool = False,
        work_dir: PureWindowsPath | None = None,
        args: list[Any] = None,
    ) -> None:
        if args is None:
            args = []
        shell_cmds = []
        if do_exit:
            shell_cmds.append("RUNEXIT.EXE")
        if work_dir:
            shell_cmds.append(f'/C:"{work_dir}"')
        shell_cmds.append(f'"{exec_path}"')
        if args:
            shell_cmds.append(" ".join([str(a) for a in args]))
        shell_cmds_str = " ".join(shell_cmds).replace("\\", r"\\")
        self.replace_string_in_file(
            SYSTEM_DRIVE / "WINDOWS" / "SYSTEM.INI",
            r"(?im)^shell=.*\r\n",
            f"shell={shell_cmds_str}\r\n",
        )
        if not mock:
            self._run_qemu()

    def run_exec(
        self,
        exec_path: PureWindowsPath | str,
        do_exit: bool = True,
        mock: bool = False,
        work_dir: PureWindowsPath | None = None,
        args: list[Any] | None = None,
    ) -> None:
        if isinstance(exec_path, str):
            exec_path = PureWindowsPath(exec_path)
        if args:
            args = [str(a) for a in args]
        return self.run_on_startup(exec_path, do_exit=do_exit, mock=mock, work_dir=work_dir, args=args)

    def gen_run_script(self, exec_path: PureWindowsPath) -> Path:
        self.run_exec(exec_path, mock=True)
        return super().gen_run_script(exec_path)
