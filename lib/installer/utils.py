import importlib
import inspect
import os
from dataclasses import asdict
from pathlib import (
    Path,
    PureWindowsPath,
)
from typing import Any

from lib.app_desc import AppDesc
from lib.dosbox.const import APP_DRIVE_LETTER
from lib.errors import DistroNotFoundException
from lib.installer.const import APP_DIR_NAME
from lib.unpack import unpack_disc_image
from lib.utils import copy


def load_vars(module_name: str) -> dict:
    constants = {}
    module = importlib.import_module(module_name)
    for name, value in inspect.getmembers(module):
        if name.isupper():
            constants[name] = value
    return constants


def unpack_cd_images_as_letters(src_dir: Path, dst_dir: Path, files: list[str], first_cd_letter: str) -> None:
    """Unpack CD images into letter folders, e.g.:

    {src_dir}/1.iso -> {dst_dir}/E
    {src_dir}/2.iso -> {dst_dir}/F
    """
    cd_letter = first_cd_letter
    for f in files:
        src_path = src_dir / f
        if not src_path.exists():
            raise DistroNotFoundException(src_path)
        unpack_disc_image(src_path, dst_dir / cd_letter)
        cd_letter = chr(ord(cd_letter) + 1)


def copy_cd_images_as_letters(src_dir: Path, dst_dir: Path, files: list[str], first_cd_letter: str) -> None:
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
    # make sure 'descr' key is part of variables for nested access
    return tmpl.format(**variables)


def subs_vars_in_task_val(v: Any, variables: dict) -> Any:
    if isinstance(v, str):
        return fstr(v, variables)
    elif isinstance(v, list):
        fmt_list = []
        for v_ in v:
            fmt_list.append(subs_vars_in_task_val(v_, variables))
        return fmt_list
    elif isinstance(v, dict):
        return subst_vars(v, variables)
    else:
        return v


def subst_vars(task: dict, variables: dict) -> dict:
    fmt_task = {}
    for k, v in task.items():
        fmt_task[k] = subs_vars_in_task_val(v, variables)
    return fmt_task


def enrich_vars(app_descr: AppDesc, installer: dict) -> dict:
    final_vars = load_vars("lib.installer.const")
    final_vars["SRC_DIR"] = str(app_descr.src_path())
    final_vars["DEST_DIR"] = str(app_descr.dst_path())
    if app_descr.runner.name in ("scummvm"):
        final_vars["DEST_APP_DIR"] = str(app_descr.dst_path() / APP_DIR_NAME)
    elif app_descr.runner.name in ("dosbox", "wine", "retroarch", "dosbox-x", "dosbox-staging", "qemu"):
        final_vars["DEST_APP_DIR"] = str(app_descr.dst_path() / APP_DRIVE_LETTER / APP_DIR_NAME)
    else:
        raise ValueError(f"unknown runner: {app_descr.runner.name}")
    final_vars["PORT_FILES_DIR"] = str(Path(os.environ.get("PORTS_ROOT_PATH")) / "games" / app_descr.app_slug / "files")
    final_vars["PORT_TEMPLATES_DIR"] = str(
        Path(os.environ.get("PORTS_ROOT_PATH")) / "games" / app_descr.app_slug / "templates"
    )
    final_vars["descr"] = asdict(app_descr)
    if "dosbox" in app_descr.runner.name:
        final_vars |= load_vars("lib.dosbox.const")
    elif app_descr.runner.name == "qemu":
        final_vars |= load_vars("lib.qemu.const")
    elif app_descr.runner.name == "wine":
        final_vars |= load_vars("lib.wine.const")
    installer_vars = installer.get("vars", None)
    if installer_vars:
        for k, v in installer_vars.items():
            installer_vars[k] = subs_vars_in_task_val(v, final_vars)
        final_vars |= installer_vars
    final_vars["item"] = "{item}"  # TODO: this is silly, just to avoid format exception for loop items
    return final_vars


def unwind_loops(root: dict, variables: dict) -> None:
    unw_tasks = []
    for t in root["tasks"]:
        cmd = list(t.keys())[0]
        task_body = t[cmd]
        if task_body:
            if "tasks" in task_body:
                task_body["tasks"] = unwind_loops(task_body, variables)
            fmt_task = subst_vars(task_body, variables)
            if "loop" in fmt_task:
                for item in fmt_task["loop"]:
                    fmt_item = subst_vars(fmt_task, variables={"item": item})
                    del fmt_item["loop"]
                    unw_tasks.append({cmd: fmt_item})
            else:
                unw_tasks.append({cmd: fmt_task})
        else:
            unw_tasks.append({cmd: {}})
    return unw_tasks


def prepare_tasks(app_descr: AppDesc, installer: dict):
    """Performs tokens substitution and loops unwinding"""
    installer["tasks"] = unwind_loops(installer, enrich_vars(app_descr, installer))


def transform_str_path(str_path: str) -> object:
    if str_path[0].isalpha():
        return PureWindowsPath(str_path)
    else:
        return Path(str_path)


def to_bool(s: str) -> bool:
    return s.lower() in ["true", "1", "t", "y", "yes"]
