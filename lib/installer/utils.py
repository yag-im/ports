import importlib
import inspect
import os
from dataclasses import asdict
from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.dosbox.const import APP_DRIVE_LETTER
from lib.errors import DistroNotFoundException
from lib.utils import copy


def load_vars(module_name: str) -> dict:
    constants = {}
    module = importlib.import_module(module_name)
    for name, value in inspect.getmembers(module):
        if name.isupper():
            constants[name] = value
    return constants


def copy_cd_images_as_letters(src_dir: Path, dst_dir: Path, files: list[str], first_cd_letter: chr) -> None:
    """Copy distro files as CD letters, e.g.:

    {src_dir}/1.iso -> {dst_dir}/E
    {src_dir}/2.iso -> {dst_dir}/F
    """
    cd_letter = first_cd_letter
    for f in files:
        src_path = src_dir / f
        if not src_path.exists():
            raise DistroNotFoundException(src_path)
        copy(src_path, dst_dir / cd_letter)
        cd_letter = chr(ord(cd_letter) + 1)


def fstr(tmpl: str, variables: dict) -> str:
    return tmpl.format(**variables)


def subst_vars(task: dict, variables: dict) -> dict:
    fmt_task = {}
    for k, v in task.items():
        if isinstance(v, str):
            fmt_task[k] = fstr(v, variables)
        elif isinstance(v, list):
            fmt_list = []
            for v_ in v:
                if isinstance(v_, str):
                    fmt_list.append(fstr(v_, variables))
                else:
                    fmt_list.append(v_)
            fmt_task[k] = fmt_list
        elif isinstance(v, dict):
            fmt_task[k] = subst_vars(v, variables)
        else:
            fmt_task[k] = v
    return fmt_task


def enrich_vars(app_descr: AppDesc, installer: dict) -> dict:
    final_vars = load_vars("lib.installer.const")
    final_vars["SRC_DIR"] = str(app_descr.src_path())
    final_vars["DEST_DIR"] = str(app_descr.dst_path())
    final_vars["DEST_APP_DIR"] = str(app_descr.dst_path() / APP_DRIVE_LETTER / "APP")
    final_vars["SRC_FILES_DIR"] = str(Path(os.environ.get("PORTS_ROOT_PATH")) / "games" / app_descr.app_slug / "files")
    final_vars["descr"] = asdict(app_descr)
    final_vars |= load_vars("lib.dosbox.const")
    installer_vars = installer.get("vars", None)
    if installer_vars:
        final_vars |= installer_vars
    final_vars["item"] = "{item}"  # TODO: this is silly, just to avoid format exception for loop items
    return final_vars


def unwind_loops(root: dict, variables: dict) -> None:
    unw_tasks = []
    for t in root["tasks"]:
        fmt_task = subst_vars(t, variables)
        if "loop" in fmt_task:
            for item in fmt_task["loop"]:
                fmt_item = subst_vars(fmt_task, variables={"item": item})
                del fmt_item["loop"]
                unw_tasks.append(fmt_item)
        else:
            if "tasks" in fmt_task:
                unwind_loops(fmt_task, variables)
            unw_tasks.append(fmt_task)
    root["tasks"] = unw_tasks


def prepare_tasks(app_descr: AppDesc, installer: dict):
    """Performs tokens substitution and loops unwinding"""
    unwind_loops(installer, enrich_vars(app_descr, installer))


def transform_str_path(str_path: str) -> object:
    if str_path[0].isalpha():
        return PureWindowsPath(str_path)
    else:
        return Path(str_path)
