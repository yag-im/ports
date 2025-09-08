import glob
import re
import shutil
import subprocess
from pathlib import (
    Path,
    PureWindowsPath,
)
from subprocess import CalledProcessError
from typing import (
    Dict,
    Union,
)

from mako.template import Template


def rm(src: Path) -> None:
    print(f"removing: {src}")
    if src.is_dir():
        shutil.rmtree(src)
    else:
        if "*" in str(src):
            for fp_str in glob.glob(str(src)):
                fp = Path(fp_str)
                fp.unlink()
        else:
            src.unlink()


def move(src: Path, dst: Path, copy_tree: bool = False) -> None:
    if isinstance(src, Path):
        src = [src]
    for s in src:
        cmd = ["mv"]

        # a*b should become a"*"b
        s = str(s).replace("*", '"*"')
        dst = str(dst).replace("*", '"*"')

        src_part = f'"{str(s)}"'
        dst_part = f'"{str(dst)}"'
        if copy_tree:
            cmd += ["-T"]
        cmd += [src_part]
        cmd += [dst_part]
        run_cmd(cmd, shell=True)  # shell=True because otherwise asterisk is not handled properly


def _copy_norm_path(path: Path):
    # escapes special symbols in paths (* and ?)
    # 3 skulls of the toltecs, Spanish version: ESPA?OL
    for sym in ("*", "?"):
        # a*b should become a"*"b, same for a?b
        path = str(path).replace(sym, f'"{sym}"')
    path = f'"{path}"'
    # now special handling for the * at the very end: "ab"*"" -> "ab"*
    if path[-3:] == f'{sym}""':
        path = path[:-2]
    return path


def copy(src: Union[Path, list[Path]], dst: Path, copy_tree: bool = False) -> None:
    """
    copies /a/* into /b/a/* when copy_tree is False (default)
    copies /a/* into /b/* when copy_tree is True
    """
    if isinstance(src, Path):
        src = [src]
    for s in src:
        cmd = ["cp", "--reflink=auto"]
        cp_prefix = "-r"
        if copy_tree:
            cp_prefix += "T"  # using T instead of "*" cos latter excludes hidden files
        if cp_prefix:
            cmd += [cp_prefix]
        cmd += [_copy_norm_path(s)]
        cmd += [_copy_norm_path(dst)]
        run_cmd(cmd, shell=True)  # shell=True because otherwise asterisk is not handled properly


def template(src: Union[Path, str], dst: Path | None, params: dict, newline: str = "\n") -> str | None:
    if isinstance(src, Path):
        with open(src, "r", encoding="UTF-8") as f:
            tmpl_input = f.read()
    else:
        tmpl_input = src
    output = Template(tmpl_input).render(**params)
    if isinstance(dst, Path):
        with open(dst, "w", newline=newline, encoding="UTF-8") as f:
            f.write(output)
    else:
        return output
    return None


def replace(file_path: Path, old: str, new: str) -> None:
    run_cmd(["sed", "-i", "-E", f"s/{old}/{new}/", str(file_path)])


def run_cmd(cmd: Union[list[str], str], env: Dict[str, str] = None, cwd: Path = None, shell: bool = False) -> None:
    if isinstance(cmd, str):
        cmd = [cmd]
    print(f"executing: {cmd}")
    subprocess.check_call(cmd if not shell else " ".join(cmd), env=env, cwd=cwd, shell=shell)


def str_in_file(file_path: Path, line: str) -> bool:
    try:
        run_cmd(["grep", "-Fq", line, file_path])
        return True
    except CalledProcessError:
        return False


def patch_macromedia_director_free_virt_mem(file_path: Path):
    # https://www.sacah.net/2008/01/how-to-edit-director-player-60-to-stop.html
    with open(file_path, mode="rb") as f:
        data = bytearray(f.read())
    target_ix = data.find(b"\x3d\x20\x75\x38\x00\x7d")  # cmp eax, 387520h; jge ...
    if target_ix == -1:
        raise ValueError("not a valid macromedia director executable")
    data[target_ix + 5] = 0xEB  # replace jge with jmp
    with open(file_path, mode="wb") as f:
        f.write(data)


def is_iso_image(file_path: Path):
    with open(file_path, "rb") as f:
        f.seek(0x8001)  # 32769 bytes offset
        signature = f.read(5)
        return signature == b"CD001"


def windows_path(path: PureWindowsPath) -> str:
    return str(path).replace("/", "\\")


def is_windows_path(path: str) -> bool:
    if not path or not isinstance(path, str):
        return False
    drive_pattern = re.compile(r"^[a-zA-Z]:[\\/].*")
    return bool(drive_pattern.match(path))
