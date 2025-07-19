from dataclasses import dataclass
from enum import StrEnum
from pathlib import (
    Path,
    PureWindowsPath,
)
from typing import (
    Any,
    Iterator,
    List,
    Union,
)


class DosMountPointType(StrEnum):
    CDROM = "cdrom"
    FLOPPY = "floppy"
    HDD = "hdd"


@dataclass
class DosMountPoint:
    letter: chr
    path: Union[Path, List[Path]]  # if list, swap CDs by Ctrl+F4
    type: DosMountPointType = DosMountPointType.CDROM
    label: str = None

    def path_str(self):
        if isinstance(self.path, List):
            return " ".join([f'"{str(p)}"' for p in self.path])
        else:
            return f'"{str(self.path)}"'

    def relative_to(self, p_base: Path):
        if isinstance(self.path, List):
            rel_path = [p.relative_to(p_base) for p in self.path]
        else:
            rel_path = self.path.relative_to(p_base)
        return DosMountPoint(self.letter, rel_path, self.label)


@dataclass
class DosMountPointCD(DosMountPoint):
    type: DosMountPointType = DosMountPointType.CDROM


@dataclass
class DosMountPointHDD(DosMountPoint):
    type: DosMountPointType = DosMountPointType.HDD


@dataclass
class DosCmdExec:
    exec_path: PureWindowsPath
    args: list[Any] = None
    cd: PureWindowsPath = None

    def __post_init__(self):
        self.exec_path = PureWindowsPath(self.exec_path)

    def iter(self) -> Iterator[str]:
        """exec_path containing full directory path should be split to multiple commands.

        Example:

            in: "F:\\GAME\\GAME.EXE", ["param1", "param2"]
            out: ["F:", "CD GAME", "GAME.EXE param1 param2"]

        When "cd" is specified, the output is slightly different:

            in: "F:\\GAME\\GAME.EXE", ["param1", "param2"], "D:\\APP"
            out: ["D:", "CD D:\\APP", "F:\\GAME\\GAME.EXE param1 param2"]
        """
        res_arr = []
        if self.cd:
            drive = self.cd.drive
            cmd_exec = [self.exec_path]
            if self.args:
                cmd_exec += self.args
            res_arr += [[drive], [f"CD {str(self.cd)}"], cmd_exec]
        else:
            drive = self.exec_path.drive
            parent = self.exec_path.parent
            if not drive or parent == self.exec_path:
                # basic built-in command, e.g. MD
                cmd_exec = [self.exec_path]
                if self.args:
                    cmd_exec += self.args
                res_arr.append(cmd_exec)
            else:
                cmd_exec = [self.exec_path.name]
                if self.args:
                    cmd_exec += self.args
                res_arr += [[drive], [f"CD {parent}"], cmd_exec]
        for cmd in res_arr:
            yield " ".join([str(part) for part in cmd])
