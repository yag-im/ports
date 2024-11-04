import pathlib

from lib.app_desc import AppDesc


class Installer:
    def __init__(self, app_desc: AppDesc):
        self.app_desc = app_desc
        pathlib.Path(app_desc.dst_path()).mkdir(parents=True, exist_ok=True)
