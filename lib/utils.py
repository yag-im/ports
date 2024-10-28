import shutil
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from typing import (
    Dict,
    List,
    Union,
)

from mako.template import Template


def rm(src: Path) -> None:
    if src.is_dir():
        shutil.rmtree(src)
    else:
        src.unlink()


def move(src: Path, dst: Path, copy_tree: bool = False) -> None:
    cmd = ["mv"]

    # a*b should become a"*"b
    src = str(src).replace("*", '"*"')
    dst = str(dst).replace("*", '"*"')

    src_part = f'"{str(src)}"'
    dst_part = f'"{str(dst)}"'
    if copy_tree:
        cmd += ["-T"]
    cmd += [src_part]
    cmd += [dst_part]
    run_cmd(cmd, shell=True)  # shell=True because otherwise asterisk is not handled properly


def _copy_norm_path(path: Path):
    # 3 skulls of the toltecs, Spanish version: ESPA?OL
    for sym in {"*", "?"}:
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
    creates destination directory if it doesn't exist in all cases
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


def template(src: Union[Path, str], dst: Union[Path, None], params: dict, newline="\n") -> Union[str, None]:
    if isinstance(src, Path):
        with open(src, "r") as f:
            input = f.read()
    else:
        input = src
    output = Template(input).render(**params)
    if isinstance(dst, Path):
        with open(dst, "w", newline=newline) as f:
            f.write(output)
    else:
        return output


def replace(file_path: Path, old: str, new: str) -> None:
    run_cmd(["sed", "-i", "-E", f"s/{old}/{new}/", str(file_path)])


def run_cmd(cmd: Union[List[str], str], env: Dict[str, str] = None, cwd: Path = None, shell: bool = False) -> None:
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
