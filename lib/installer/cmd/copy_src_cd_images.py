import re
from pathlib import Path

from lib.app_desc import AppDesc
from lib.errors import DistroNotFoundException
from lib.installer.const import FIRST_CD_DRIVE_LETTER
from lib.installer.utils import copy_cd_images_as_letters
from lib.utils import copy


def run(task: dict, app_descr: AppDesc) -> None:
    """Copy source CD images into the app destination.

    Behavior:
    - Implicitly uses the list of files declared in `app_descr.distro.files`.
    - If any of the declared files are CUE files (case-insensitive), treat the
      distro as cue-based: for each CUE file, parse referenced FILE entries and
      copy the CUE and each referenced file from the source directory to the
      destination. Do not rename these files on copy.
    - Otherwise, treat the distro as plain CD images and
      copy the files listed in `app_descr.distro.files` into single-letter named files in
       destination directory starting from `FIRST_CD_DRIVE_LETTER` (or
      overridden by the task's `first_cd_drive_letter`).

    Parameters:
    - task: installer task dict (may include `first_cd_drive_letter`).
    - app_descr: application description (provides `src_path`, `dst_path`, and
      `distro.files`).

    Raises:
    - DistroNotFoundException if a required file (cue or referenced file) is
      missing in the source directory or if `distro.files` is empty when
      expected.
    """
    src_path = app_descr.src_path()
    dst_path = app_descr.dst_path()

    # determine files from distro description
    distro_files = app_descr.distro.files
    # find .cue files among declared distro files (case-insensitive)
    cue_files = [src_path / f for f in distro_files if Path(f).suffix.lower() == ".cue"]

    if cue_files:
        # For cue-based images, copy the cue and the files referenced from it.
        for cue in cue_files:
            cue_file_path = src_path / cue
            if not cue_file_path.exists():
                raise DistroNotFoundException(cue_file_path)
            content = cue_file_path.read_text(encoding="utf-8", errors="ignore")
            # find FILE entries. Matches lines like: FILE "name.bin" BINARY or FILE name.bin BINARY
            refs = re.findall(r"^\s*FILE\s+\"?([^\"\n]+)\"?", content, flags=re.IGNORECASE | re.MULTILINE)
            if not refs:
                raise DistroNotFoundException(cue_file_path)
            ref_paths = []
            for ref in refs:
                # try referenced path as-is relative to src_path
                candidate = src_path / ref
                if not candidate.exists():
                    raise DistroNotFoundException(candidate)
                ref_paths.append(candidate)

            # copy referenced files and the cue file itself
            # copy() will place the files into dst_path preserving basenames
            copy(ref_paths, dst_path)
            copy(cue_file_path, dst_path)
    else:
        copy_cd_images_as_letters(
            src_dir=src_path,
            dst_dir=dst_path,
            files=distro_files,
            first_cd_letter=task.get("first_cd_drive_letter", FIRST_CD_DRIVE_LETTER),
        )
