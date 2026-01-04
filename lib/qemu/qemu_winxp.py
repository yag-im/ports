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
    Union,
)

from lib.app_desc import AppDesc
from lib.qemu.const import (
    APP_DRIVE,
    SYSTEM_DRIVE,
)
from lib.qemu.qemu import (
    Qemu,
    QemuConf,
    QemuFlavor,
)
from lib.utils import template

# pylint: disable=useless-parent-delegation

BASE_CPU = "Skylake-Server,model-id=Intel"
BASE_MEMORY = 1024

BASE_SCREEN_WIDTH = 800
BASE_COLOR_BITS = 32
BASE_AUDIO_DEVICE = "AC97"


@dataclass
class QemuWinXpConf(QemuConf):
    flavor: QemuFlavor = field(default=QemuFlavor.WINXPSP3)
    cpu: str = BASE_CPU
    memory: int = BASE_MEMORY
    color_bits: int = BASE_COLOR_BITS
    screen_width: int = BASE_SCREEN_WIDTH
    audio_device: str = BASE_AUDIO_DEVICE
    reg_file_encoding: str = "utf-16"
    pointer_device: str | None = None


class QemuWinXp(Qemu[QemuWinXpConf]):
    def __init__(self, root_dir: Path, app_descr: AppDesc, conf: QemuWinXpConf = QemuWinXpConf()) -> None:
        super().__init__(root_dir, app_descr, conf)

    def set_display_params(self, screen_width: int, screen_height, color_bits: int):
        self.run_exec(
            "QRES",
            args=[
                "/X",
                screen_width,
                "/Y",
                screen_height,
                "/C",
                color_bits,
            ],
        )

    def run_on_startup(
        self,
        cmd: Union[str, list[str]],
        do_exit: bool = True,
        mock: bool = False,
        work_dir: PureWindowsPath | None = None,
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
            if work_dir:
                dest_path = work_dir
            else:
                dest_path = f"{SYSTEM_DRIVE}\\Documents and Settings\\gamer\\Start Menu\\Programs\\Startup"
                if self.conf.lang == "ru":
                    dest_path = f"{SYSTEM_DRIVE}\\Documents and Settings\\gamer\\Главное меню\\Программы\\Автозагрузка"
                elif self.conf.flavor == QemuFlavor.WIN98SE:
                    dest_path = f"{SYSTEM_DRIVE}\\Windows\\Start Menu\\Programs\\StartUp"
                    if self.conf.lang == "ru":
                        dest_path = f"{SYSTEM_DRIVE}\\Windows\\Главное меню\\Программы\\Автозагрузка"
            self.copy(
                tmp_runexit_bat,
                PureWindowsPath(dest_path),
            )
        if not mock:
            self._run_qemu()

    def run_exec(
        self,
        exec_path: PureWindowsPath | str,
        do_exit: bool = True,
        mock: bool = False,
        work_dir: PureWindowsPath | None = None,  # runexit script dir
        args: list[Any] | None = None,
    ) -> None:
        if isinstance(exec_path, str):
            exec_path = PureWindowsPath(exec_path)

        cmd = ["start", "/wait", '""', "/D", f'"{str(exec_path.parent)}"', f'"{exec_path}"']
        if args:
            args = [str(a) for a in args]
            cmd += args
        return self.run_on_startup(" ".join(cmd), do_exit=do_exit, mock=mock, work_dir=work_dir)

    def gen_run_script(self, exec_path: PureWindowsPath, do_exit: bool = True, args: list[Any] | None = None) -> Path:
        # just copying RUNEXIT.BAT for apps' exec into D: drive, no runs
        self.run_exec(exec_path, do_exit=do_exit, mock=True, work_dir=PureWindowsPath(APP_DRIVE), args=args)
        self.upd_reg(
            {
                "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon": [
                    {"Shell": PureWindowsPath(f"{APP_DRIVE}\\RUNEXIT.BAT")}
                ]
            }
        )
        return super().gen_run_script(exec_path)
