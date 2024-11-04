import os
import tempfile
from pathlib import Path
from subprocess import CalledProcessError
from typing import List

from lib.utils import (
    move,
    run_cmd,
)

SEVENZ_EXEC = os.getenv("SEVENZ_EXEC")


def run_7z(src, dest, extract_files=None, copy_tree=False):
    extract_cmd = "e" if copy_tree else "x"
    cmd = [SEVENZ_EXEC, extract_cmd, src, f"-o{dest}", "-y"]
    if extract_files:
        cmd += extract_files
    try:
        run_cmd(cmd)
    except CalledProcessError as e:
        if e.returncode == 2:
            # e.g. when filename contains non-latin characters (e.g. 3 Skulls of the toltecs, Spanish version)
            # files unpack fine, but 7z returns an error
            print("7z has failed, but we'll try to continue...")


def unpack_archive(src: Path, dest: Path, extract_files: List[str] = None, creates: Path = None) -> None:
    assert src.exists()
    dest.mkdir(parents=True, exist_ok=True)

    image_format = src.suffix.lower()[1:]
    # sh - gog's mojosetup
    if image_format in {"zip", "sh"}:
        try:
            run_cmd(["unzip", str(src), "-d", str(dest)])
        except Exception:  # pylint: disable=W0718
            pass  # mojosetup returns non-zero exit status
    elif image_format == "cab":
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            run_cmd(["unshield", "-d", Path(td), "-D", "2", "x", str(src)])
            move(tmp_path / "Program_Executable_Files", dest, copy_tree=True)
    elif image_format == "rar":
        run_cmd(["unrar", "-x", str(src), str(dest)])
    else:
        run_7z(src, dest, extract_files)
        if creates and not creates.exists():
            print(f"error: extracted archive doesn't contain expected file: {creates}, installer might be corrupted")


def unpack_disc_image(
    src: Path, dest: Path, extract_files: List[str] = None, creates: Path = None, copy_tree=False
) -> None:
    assert src.exists()
    dest.mkdir(exist_ok=True, parents=True)

    image_format = src.suffix.lower()[1:]

    if image_format == "iso":
        run_7z(src, dest, extract_files, copy_tree)
    elif image_format in ["nrg", "mdf", "pdi", "cdi", "bin", "cue", "b5i", "img"]:
        # create intermediate ISO
        with tempfile.TemporaryDirectory() as td:
            tmp_iso_image = Path(td) / "tmp.iso"
            run_cmd(["iat", src, tmp_iso_image])
            run_7z(tmp_iso_image, dest, extract_files, copy_tree)
    else:
        raise ValueError(f"Unrecognized image format: {image_format}")

    if creates and not creates.exists():
        print(f"error: extracted archive doesn't contain expected file: {creates}, installer might be corrupted")


def unpack_innoextract(src: Path, dest: Path, creates: Path, is_gog: bool = False) -> None:
    assert src.exists()
    dest.mkdir(exist_ok=True)
    cmd_args = ["innoextract", "--extract"]
    if is_gog:
        cmd_args += ["--exclude-temp", "--gog"]
    cmd_args += ["--output-dir", str(dest)]
    cmd_args.append(str(src))
    run_cmd(cmd_args)
    if not creates.exists():
        raise ValueError(
            f"error: extracted archive doesn't contain expected file: {creates}, installer might be corrupted"
        )
