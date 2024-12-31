import os
import tempfile
from pathlib import Path
from subprocess import CalledProcessError
from typing import (
    List,
    Optional,
)

from lib.utils import (
    copy,
    move,
    run_cmd,
)

SEVENZ_EXEC = os.getenv("SEVENZ_EXEC")


def run_7z(src: Path, dest: Path, extract_files: Optional[list[str]] = None):
    # 7z "e" doesn't work as it always eliminate all inner directories recursively
    # so we first extract into the temp dir using "x", and then move files into dest dir honoring copy_tree behavior
    # (when extract files contain '*')
    if extract_files:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            cmd = [SEVENZ_EXEC, "x", src, f"-o{tmp_path}", "-y"]
            cmd += extract_files
    else:
        cmd = [SEVENZ_EXEC, "x", src, f"-o{dest}", "-y"]
    try:
        run_cmd(cmd)
    except CalledProcessError as e:
        if e.returncode == 2:
            # e.g. when filename contains non-latin characters (e.g. 3 Skulls of the toltecs, Spanish version)
            # files unpack fine, but 7z returns an error
            print("7z has failed, but we'll try to proceed...")
    if extract_files:
        # do not use move; TODO: move a/b to c when c/b exists fails
        copy([tmp_path / ef for ef in extract_files], dest, copy_tree=False)


def run_unzip(src: Path, dest: Path, extract_files=None):
    if extract_files:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_cmd(["unzip", "-o", str(src), "-d", str(tmp_path)])
            # do not use move; TODO: move a/b to c when c/b exists fails
            copy([tmp_path / ef for ef in extract_files], dest, copy_tree=False)
    else:
        run_cmd(["unzip", "-o", str(src), "-d", str(dest)])


def unpack_archive(src: Path, dest: Path, extract_files: List[str] = None, creates: Path = None) -> None:
    if not src.exists():
        raise ValueError(f"src doesn't exist: {src}")
    dest.mkdir(parents=True, exist_ok=True)

    image_format = src.suffix.lower()[1:]
    # sh - gog's mojosetup
    if image_format in {"zip", "sh"}:
        try:
            run_unzip(src, dest, extract_files)
        except Exception:  # pylint: disable=W0718
            pass  # mojosetup returns non-zero exit status
    elif image_format == "cab":
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            run_cmd(["unshield", "-d", Path(td), "-D", "2", "x", str(src)])
            move(tmp_path / "Program_Executable_Files", dest, copy_tree=True)
    elif image_format == "rar":
        cmd = ["unrar", "-x", str(src)]
        if extract_files:
            cmd += extract_files
        cmd.append(str(dest))
        run_cmd(cmd)
    else:
        run_7z(src, dest, extract_files)
        if creates and not creates.exists():
            print(f"error: extracted archive doesn't contain expected file: {creates}, installer might be corrupted")


def unpack_disc_image(src: Path, dest: Path, extract_files: List[str] = None, creates: Path = None) -> None:
    assert src.exists()
    dest.mkdir(exist_ok=True, parents=True)

    image_format = src.suffix.lower()[1:]

    if image_format == "iso":
        run_7z(src, dest, extract_files)
    elif image_format in ["nrg", "mdf", "pdi", "cdi", "bin", "cue", "b5i", "img"]:
        # create intermediate ISO
        with tempfile.TemporaryDirectory() as td:
            tmp_iso_image = Path(td) / "tmp.iso"
            run_cmd(["iat", src, tmp_iso_image])
            run_7z(tmp_iso_image, dest, extract_files)
    else:
        raise ValueError(f"Unrecognized image format: {image_format}")

    if creates and not creates.exists():
        print(f"error: extracted archive doesn't contain expected file: {creates}, installer might be corrupted")


def unpack_innoextract(
    src: Path, dest: Path, creates: Path = None, is_gog: bool = False, files: list[str] = None
) -> None:
    if not src.exists():
        raise ValueError(f"src path doesn't exist: {src}")
    if not files:
        files = "*"
    dest.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir)
        cmd_args = ["innoextract", "--extract"]
        if is_gog:
            cmd_args += ["--exclude-temp", "--gog"]
        cmd_args += ["--output-dir", str(tmp_path)]
        cmd_args.append(str(src))
        run_cmd(cmd_args)
        if creates and not (tmp_path / creates.name).exists():
            raise ValueError(
                f"error: extracted archive doesn't contain expected file: {creates}, installer might be corrupted"
            )
        copy([tmp_path / ef for ef in files], dest, copy_tree=False)
